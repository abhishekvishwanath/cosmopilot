import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ClinicPrincipal, get_current_clinic_staff
from app.db.session import get_db
from app.repositories import conversations as conversations_repo
from app.schemas.conversation import ConversationRead, MessageRead

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error": {"code": "not_found", "message": "Conversation not found.", "details": {}}
        },
    )


@router.get("", response_model=list[ConversationRead])
async def list_conversations(
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
    lead_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[ConversationRead]:
    conversations = await conversations_repo.list_conversations(
        db, principal.clinic_id, lead_id=lead_id
    )
    return [ConversationRead.model_validate(c) for c in conversations]


@router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: uuid.UUID,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConversationRead:
    conversation = await conversations_repo.get_conversation(
        db, principal.clinic_id, conversation_id
    )
    if conversation is None:
        raise _not_found()
    return ConversationRead.model_validate(conversation)


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MessageRead]:
    conversation = await conversations_repo.get_conversation(
        db, principal.clinic_id, conversation_id
    )
    if conversation is None:
        raise _not_found()
    messages = await conversations_repo.list_messages(db, conversation_id)
    return [MessageRead.model_validate(m) for m in messages]
