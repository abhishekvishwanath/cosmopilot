"""
AI Concierge orchestration (CLAUDE.md §10, Phase 6). Owns the tool-calling
loop and conversation persistence; the LLM never controls workflow state
directly (CLAUDE.md §5.3) — every state change happens inside a tool
handler that the *service layer* validates, same as the rest of the app.
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.prompts import build_system_prompt
from app.agents.tools import (
    TOOL_HANDLERS,
    TOOL_SCHEMAS,
    ToolContext,
    ToolError,
    escalate_to_human,
)
from app.core.logging import log_with_fields
from app.models.clinic import Clinic
from app.models.conversation import Conversation
from app.models.lead import Lead
from app.providers.llm import get_llm_provider
from app.providers.llm.base import ChatMessage
from app.providers.llm.ollama import OllamaError
from app.repositories import catalog as catalog_repo
from app.repositories import conversations as conversations_repo
from app.services import leads as leads_service

logger = logging.getLogger("cosmopilot.concierge")

# A hard ceiling on how many tool round-trips one turn can make — never
# trust the model to stop on its own (CLAUDE.md §5.3). If it's hit, the
# turn deterministically escalates rather than looping forever or
# guessing.
MAX_TOOL_ITERATIONS = 4

# Deterministic backstop, not a replacement for the LLM calling
# escalate_to_human itself (CLAUDE.md §5.3 — critical state changes
# shouldn't depend solely on model reliability). Narrow and explicit on
# purpose — broad keyword-matching on medical/pain terms would be fragile
# and error-prone; this only catches the one case that's both unambiguous
# and highest-stakes to miss: a visitor plainly asking for a person.
_EXPLICIT_HUMAN_REQUEST_PHRASES = (
    "speak to a human",
    "speak to a person",
    "speak with a human",
    "speak with a person",
    "talk to a human",
    "talk to a person",
    "talk to someone",
    "real person",
    "human agent",
    "speak to someone",
)


def _requests_human(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in _EXPLICIT_HUMAN_REQUEST_PHRASES)


@dataclass(frozen=True)
class ToolCallTrace:
    name: str
    arguments: dict
    result: dict


@dataclass(frozen=True)
class ConciergeTurnResult:
    conversation_id: uuid.UUID
    reply: str
    lead_status: str
    tool_calls: list[ToolCallTrace] = field(default_factory=list)


class ConversationMismatchError(Exception):
    """The given conversation_id doesn't belong to this clinic/lead."""


async def get_or_create_conversation(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    lead_id: uuid.UUID,
    conversation_id: uuid.UUID | None,
    channel: str = "web_chat",
) -> Conversation:
    if conversation_id is not None:
        conversation = await conversations_repo.get_conversation(db, clinic_id, conversation_id)
        if conversation is None or conversation.lead_id != lead_id:
            raise ConversationMismatchError("Conversation not found for this lead.")
        return conversation
    return await conversations_repo.create_conversation(db, clinic_id, lead_id, channel)


async def _load_history(db: AsyncSession, conversation_id: uuid.UUID) -> list[ChatMessage]:
    messages = await conversations_repo.list_messages(db, conversation_id)
    history: list[ChatMessage] = []
    for m in messages:
        role: Literal["user", "assistant"] = "user" if m.sender_type == "patient" else "assistant"
        history.append({"role": role, "content": m.content})
    return history


async def _lead_treatment_name(db: AsyncSession, clinic_id: uuid.UUID, lead: Lead) -> str | None:
    if lead.treatment_id is None:
        return None
    treatment = await catalog_repo.get_treatment(db, clinic_id, lead.treatment_id)
    return treatment.name if treatment else None


def _lead_summary(lead: Lead) -> str:
    parts = [f"name: {lead.name}", f"status: {lead.status}"]
    if lead.phone:
        parts.append(f"phone: {lead.phone}")
    return ", ".join(parts)


async def handle_turn(
    db: AsyncSession,
    clinic: Clinic,
    lead: Lead,
    conversation: Conversation,
    user_message: str,
) -> ConciergeTurnResult:
    await conversations_repo.create_message(
        db, conversation.id, direction="inbound", sender_type="patient", content=user_message
    )

    treatment_name = await _lead_treatment_name(db, clinic.id, lead)
    system_prompt = build_system_prompt(
        clinic_name=clinic.name,
        treatment_name=treatment_name,
        lead_summary=_lead_summary(lead),
    )
    history = await _load_history(db, conversation.id)
    # A reminder re-injected right before the newest question, not just
    # once at the very start — empirically, without this, qwen2.5:7b
    # reliably calls the right tool on an isolated first question but
    # starts answering later turns straight from its own (sometimes
    # wrong) assumptions once a few turns of clean-looking conversation
    # history have built up, since the persisted history only shows final
    # text and not the tool calls that produced it. Keeping the
    # instruction close to the point of generation, not just at position
    # 0 of a growing context, is what actually holds it.
    reminder: ChatMessage = {
        "role": "system",
        "content": (
            "Reminder: for ANY factual claim — hours, pricing, doctor names/credentials, "
            "policies, treatment specifics — call the matching tool now, even if a similar "
            "question was already answered earlier in this conversation. Never answer from "
            "memory or assumption."
        ),
    }
    chat_messages: list[ChatMessage] = [
        {"role": "system", "content": system_prompt},
        *history[:-1],
        reminder,
        *history[-1:],
    ]

    ctx = ToolContext(db=db, clinic_id=clinic.id, clinic_name=clinic.name, lead=lead)
    llm = get_llm_provider()
    tool_trace: list[ToolCallTrace] = []
    final_text: str | None = None

    try:
        for _ in range(MAX_TOOL_ITERATIONS):
            response = await llm.chat(messages=chat_messages, tools=TOOL_SCHEMAS)

            if not response.tool_calls:
                final_text = response.content or (
                    "Sorry, could you rephrase that? I want to make sure I understand."
                )
                break

            chat_messages.append({"role": "assistant", "content": response.content or ""})
            for call in response.tool_calls:
                handler = TOOL_HANDLERS.get(call.name)
                if handler is None:
                    result: dict = {"error": f"Unknown tool '{call.name}'."}
                else:
                    try:
                        result = await handler(ctx, **call.arguments)
                    except ToolError as exc:
                        result = {"error": str(exc)}
                    except Exception:
                        log_with_fields(
                            logger,
                            logging.ERROR,
                            "tool_execution_failed",
                            tool=call.name,
                            clinic_id=str(clinic.id),
                            exc_info=True,
                        )
                        result = {"error": "This action failed unexpectedly."}

                log_with_fields(
                    logger,
                    logging.INFO,
                    "tool_call",
                    tool=call.name,
                    arguments=call.arguments,
                    clinic_id=str(clinic.id),
                    lead_id=str(ctx.lead.id) if ctx.lead else None,
                )
                tool_trace.append(
                    ToolCallTrace(name=call.name, arguments=call.arguments, result=result)
                )
                chat_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "name": call.name,
                        "content": json.dumps(result, default=str),
                    }
                )
        else:
            # Hit MAX_TOOL_ITERATIONS without a final answer — deterministic
            # safety net, not a judgment call left to the model.
            final_text = (
                "I want to make sure you get accurate information, so I'm looping in the "
                "clinic team directly — they'll follow up with you shortly."
            )
            await leads_service.transition_lead_status(db, lead, "HUMAN_REQUIRED")
    except OllamaError as exc:
        log_with_fields(
            logger,
            logging.WARNING,
            "concierge_llm_unavailable",
            clinic_id=str(clinic.id),
            error=str(exc),
        )
        final_text = (
            "I'm having trouble connecting right now. I'll have the clinic team follow up "
            "with you directly — you can also reach us on WhatsApp."
        )
        await leads_service.transition_lead_status(db, lead, "HUMAN_REQUIRED")

    assert final_text is not None  # every branch above sets it

    already_escalated = any(t.name == "escalate_to_human" for t in tool_trace)
    if not already_escalated and _requests_human(user_message):
        result = await escalate_to_human(ctx, reason="visitor explicitly asked for a human")
        tool_trace.append(
            ToolCallTrace(
                name="escalate_to_human",
                arguments={"reason": "visitor explicitly asked for a human"},
                result=result,
            )
        )
        log_with_fields(
            logger,
            logging.INFO,
            "deterministic_escalation_backstop_triggered",
            clinic_id=str(clinic.id),
            lead_id=str(lead.id),
        )

    trace_metadata = (
        {
            "tool_calls": [
                {"name": t.name, "arguments": t.arguments, "result": t.result} for t in tool_trace
            ]
        }
        if tool_trace
        else None
    )
    await conversations_repo.create_message(
        db,
        conversation.id,
        direction="outbound",
        sender_type="ai",
        content=final_text,
        tool_name=tool_trace[-1].name if tool_trace else None,
        metadata=trace_metadata,
    )

    # Refresh the lead — tool handlers (e.g. escalate_to_human,
    # create_appointment_intent) may have changed its status via ctx.lead,
    # the same row `lead` here refers to (handle_turn always starts ctx
    # with a non-None lead, and no tool handler reassigns ctx.lead when it
    # was already set — see create_lead's early-return guard in tools.py).
    await db.refresh(lead)

    return ConciergeTurnResult(
        conversation_id=conversation.id,
        reply=final_text,
        lead_status=lead.status,
        tool_calls=tool_trace,
    )


async def summarize_conversation(db: AsyncSession, conversation: Conversation) -> str:
    """
    CLAUDE.md's "structured summary" deliverable — regenerated after each
    turn so the CRM lead record (§19) always reflects the latest state,
    not just what happened at hand-off time.
    """
    messages = await conversations_repo.list_messages(db, conversation.id)
    if not messages:
        return ""

    transcript = "\n".join(f"{m.sender_type}: {m.content}" for m in messages)
    llm = get_llm_provider()
    response = await llm.generate(
        system=(
            "Summarize this patient conversation with a dental clinic's AI concierge in 2-3 "
            "sentences: what the patient wants, key facts established, and the current status. "
            "Be factual — don't add anything not actually said in the conversation."
        ),
        context=transcript,
        question="Provide a structured summary of this conversation so far.",
    )
    await conversations_repo.update_conversation(db, conversation, {"summary": response.text})
    return response.text
