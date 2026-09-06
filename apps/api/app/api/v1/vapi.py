"""
Inbound events from Vapi (CLAUDE.md §15/§24, Phase 10). Vapi is call
transport only — every tool call it forwards here dispatches to the exact
same `TOOL_HANDLERS` the text Concierge uses (app/agents/tools.py), so
voice and chat share one deterministic backend, never a second copy of
the assistant's logic (CLAUDE.md §7).

Body shape is Vapi's own `{"message": {...}}` envelope, discriminated by
`message.type`. We only act on the three message types the assistant is
actually configured to send (see scripts/create_vapi_assistant.py) —
anything else is accepted and ignored rather than rejected, since Vapi's
message catalog is large and growing and an unrecognized-but-harmless
message must never fail the webhook (CLAUDE.md §25).
"""

import json
import logging
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.tools import TOOL_HANDLERS, ToolContext, ToolError
from app.core.logging import log_with_fields
from app.core.security import verify_vapi_webhook
from app.db.session import get_db
from app.repositories import clinics as clinics_repo
from app.repositories import conversations as conversations_repo
from app.repositories import events as events_repo
from app.repositories import leads as leads_repo
from app.services import leads as leads_service
from app.services.n8n import notify_call_unanswered

logger = logging.getLogger("cosmopilot.webhooks.vapi")

router = APIRouter(
    prefix="/webhooks/vapi",
    tags=["webhooks"],
    dependencies=[Depends(verify_vapi_webhook)],
)

# endedReason values (from Vapi's own enum) that mean the patient never
# actually engaged — everything else (customer-ended-call, an assistant
# hangup after a real exchange, etc) counts as answered. Deliberately a
# narrow allow-list of "definitely no answer" reasons rather than the
# inverse, so an unrecognized future reason defaults to the side that
# doesn't skip a genuinely-answered lead straight to the WhatsApp fallback.
_NO_ANSWER_REASONS = {
    "customer-did-not-answer",
    "customer-busy",
    "voicemail",
    "call.forwarding.no-answer",
}


def _call_metadata(message: dict[str, Any]) -> dict[str, Any]:
    call = message.get("call") or {}
    overrides = call.get("assistantOverrides") or {}
    return overrides.get("metadata") or {}


async def _handle_tool_calls(db: AsyncSession, message: dict[str, Any]) -> dict[str, Any]:
    metadata = _call_metadata(message)
    tool_calls = message.get("toolWithToolCallList") or []
    raw_ids = [
        (item.get("toolCall") or {}).get("id") for item in tool_calls if item.get("toolCall")
    ]

    clinic_id_raw = metadata.get("clinic_id")
    lead_id_raw = metadata.get("lead_id")
    if not clinic_id_raw:
        return {
            "results": [
                {"toolCallId": tc_id, "error": "No clinic on this call."} for tc_id in raw_ids
            ]
        }

    clinic = await clinics_repo.get_clinic(db, uuid.UUID(clinic_id_raw))
    if clinic is None:
        return {
            "results": [{"toolCallId": tc_id, "error": "Clinic not found."} for tc_id in raw_ids]
        }

    lead = None
    if lead_id_raw:
        lead = await leads_repo.get_lead(db, clinic.id, uuid.UUID(lead_id_raw))

    ctx = ToolContext(db=db, clinic_id=clinic.id, clinic_name=clinic.name, lead=lead)
    results: list[dict[str, Any]] = []
    for item in tool_calls:
        tool_call = item.get("toolCall") or {}
        tool_call_id = tool_call.get("id", "")
        function = tool_call.get("function") or {}
        name = function.get("name", "")
        try:
            arguments = json.loads(function.get("arguments") or "{}")
        except json.JSONDecodeError:
            arguments = {}

        handler = TOOL_HANDLERS.get(name)
        if handler is None:
            results.append({"toolCallId": tool_call_id, "error": f"Unknown tool '{name}'."})
            continue
        try:
            result = await handler(ctx, **arguments)
            results.append({"toolCallId": tool_call_id, "result": json.dumps(result, default=str)})
        except ToolError as exc:
            results.append({"toolCallId": tool_call_id, "error": str(exc)})
        except Exception:
            log_with_fields(
                logger,
                logging.ERROR,
                "vapi_tool_execution_failed",
                tool=name,
                clinic_id=clinic_id_raw,
                exc_info=True,
            )
            results.append(
                {"toolCallId": tool_call_id, "error": "This action failed unexpectedly."}
            )

        log_with_fields(
            logger,
            logging.INFO,
            "vapi_tool_call",
            tool=name,
            arguments=arguments,
            clinic_id=clinic_id_raw,
            lead_id=str(ctx.lead.id) if ctx.lead else None,
        )

    await db.commit()
    return {"results": results}


async def _handle_end_of_call_report(db: AsyncSession, message: dict[str, Any]) -> None:
    metadata = _call_metadata(message)
    clinic_id_raw = metadata.get("clinic_id")
    lead_id_raw = metadata.get("lead_id")
    if not clinic_id_raw or not lead_id_raw:
        log_with_fields(
            logger, logging.WARNING, "vapi_end_of_call_report_missing_metadata", metadata=metadata
        )
        return

    clinic_id = uuid.UUID(clinic_id_raw)
    lead = await leads_repo.get_lead(db, clinic_id, uuid.UUID(lead_id_raw))
    if lead is None or lead.status != "CONTACTING":
        # Idempotent: a lead already resolved another way (or a duplicate
        # webhook delivery) is left alone rather than double-processed
        # (CLAUDE.md §24).
        return

    ended_reason = message.get("endedReason", "")
    answered = ended_reason not in _NO_ANSWER_REASONS
    new_status = "CONTACTED" if answered else "NO_ANSWER"
    await leads_service.transition_lead_status(db, lead, new_status)

    summary = (message.get("analysis") or {}).get("summary")
    if summary:
        conversation = await conversations_repo.get_latest_conversation_by_channel(
            db, clinic_id, lead.id, "voice"
        )
        if conversation is None:
            conversation = await conversations_repo.create_conversation(
                db, clinic_id, lead.id, "voice"
            )
        await conversations_repo.update_conversation(db, conversation, {"summary": summary})

    await events_repo.create_event(
        db,
        clinic_id=clinic_id,
        event_type="ai_call_ended",
        source="vapi",
        lead_id=lead.id,
        metadata={"ended_reason": ended_reason, "outcome": new_status},
    )
    await db.commit()

    log_with_fields(
        logger, logging.INFO, "vapi_end_of_call_report", lead_id=str(lead.id), outcome=new_status
    )
    if new_status == "NO_ANSWER":
        await notify_call_unanswered(lead.id, clinic_id)


@router.post("")
async def handle_vapi_webhook(
    request: Request, db: Annotated[AsyncSession, Depends(get_db)]
) -> dict[str, Any]:
    body = await request.json()
    message = body.get("message") or {}
    message_type = message.get("type")

    if message_type == "tool-calls":
        return await _handle_tool_calls(db, message)
    if message_type == "end-of-call-report":
        await _handle_end_of_call_report(db, message)
        return {}

    log_with_fields(logger, logging.INFO, "vapi_webhook_ignored", message_type=message_type)
    return {}
