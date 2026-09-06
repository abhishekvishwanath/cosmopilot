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


async def get_latest_conversation_by_channel(
    db: AsyncSession, clinic_id: uuid.UUID, lead_id: uuid.UUID, channel: str
) -> Conversation | None:
    """Reuses the lead's existing thread on a channel (e.g. a WhatsApp
    follow-up should land in the same conversation as any prior WhatsApp
    message, not fork a new one each time n8n sends a follow-up)."""
    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.clinic_id == clinic_id,
            Conversation.lead_id == lead_id,
            Conversation.channel == channel,
        )
        .order_by(Conversation.created_at.desc())
    )
    return result.scalars().first()


async def list_messages(db: AsyncSession, conversation_id: uuid.UUID) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.asc())
    )
    return list(result.scalars().all())


async def create_conversation(
    db: AsyncSession, clinic_id: uuid.UUID, lead_id: uuid.UUID, channel: str
) -> Conversation:
    conversation = Conversation(
        clinic_id=clinic_id, lead_id=lead_id, channel=channel, status="active"
    )
    db.add(conversation)
    await db.flush()
    return conversation


async def update_conversation(
    db: AsyncSession, conversation: Conversation, data: dict
) -> Conversation:
    for field, value in data.items():
        setattr(conversation, field, value)
    await db.flush()
    return conversation


async def create_message(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    direction: str,
    sender_type: str,
    content: str,
    tool_name: str | None = None,
    metadata: dict | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        direction=direction,
        sender_type=sender_type,
        content=content,
        tool_name=tool_name,
        message_metadata=metadata,
    )
    db.add(message)
    await db.flush()
    return message
