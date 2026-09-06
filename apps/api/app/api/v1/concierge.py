import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import concierge as concierge_agent
from app.core.logging import log_with_fields
from app.core.security import ClinicPrincipal, get_current_clinic_staff
from app.db.session import get_db
from app.providers.llm.ollama import OllamaError
from app.repositories import clinics as clinics_repo
from app.repositories import leads as leads_repo
from app.schemas.concierge import ConciergeMessageRequest, ConciergeMessageResponse, ToolCallRead

logger = logging.getLogger("cosmopilot.concierge.api")

router = APIRouter(prefix="/leads/{lead_id}/concierge", tags=["concierge"])


def _not_found(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": {"code": "not_found", "message": message, "details": {}}},
    )


@router.post("/messages", response_model=ConciergeMessageResponse)
async def send_concierge_message(
    lead_id: uuid.UUID,
    payload: ConciergeMessageRequest,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConciergeMessageResponse:
    """
    Staff-only test console for the AI Concierge (CLAUDE.md Phase 6's "Run
    conversation tests" checkpoint) — lets a staff member simulate a
    patient's side of the conversation against any real lead, using the
    exact same orchestration the public widget uses.
    """
    lead = await leads_repo.get_lead(db, principal.clinic_id, lead_id)
    if lead is None:
        raise _not_found("Lead not found.")

    clinic = await clinics_repo.get_clinic(db, principal.clinic_id)
    if clinic is None:
        raise _not_found("Clinic not found.")

    try:
        conversation = await concierge_agent.get_or_create_conversation(
            db, principal.clinic_id, lead.id, payload.conversation_id
        )
    except concierge_agent.ConversationMismatchError as exc:
        raise _not_found(str(exc)) from exc

    result = await concierge_agent.handle_turn(db, clinic, lead, conversation, payload.message)
    await db.commit()

    try:
        await concierge_agent.summarize_conversation(db, conversation)
        await db.commit()
    except OllamaError:
        log_with_fields(
            logger,
            logging.WARNING,
            "summary_generation_failed",
            conversation_id=str(conversation.id),
        )

    return ConciergeMessageResponse(
        conversation_id=result.conversation_id,
        reply=result.reply,
        lead_status=result.lead_status,
        tool_calls=[
            ToolCallRead(name=t.name, arguments=t.arguments, result=t.result)
            for t in result.tool_calls
        ],
    )
