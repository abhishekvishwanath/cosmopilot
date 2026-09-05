import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message


async def list_conversations(
    db: AsyncSession, clinic_id: uuid.UUID, lead_id: uuid.UUID | None = None
) -> list[Conversation]:
    query = select(Conversation).where(Conversation.clinic_id == clinic_id)
    if lead_id:
        query = query.where(Conversation.lead_id == lead_id)
    query = query.order_by(Conversation.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_conversation(
    db: AsyncSession, clinic_id: uuid.UUID, conversation_id: uuid.UUID
) -> Conversation | None:
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.clinic_id == clinic_id
        )
    )
    return result.scalars().first()


async def list_messages(db: AsyncSession, conversation_id: uuid.UUID) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.asc())
    )
    return list(result.scalars().all())
