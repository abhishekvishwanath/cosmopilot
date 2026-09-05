import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPkMixin

ConversationChannel = Enum("voice", "whatsapp", "web_chat", name="conversation_channel")
MessageDirection = Enum("inbound", "outbound", name="message_direction")
MessageSenderType = Enum("patient", "ai", "staff", name="message_sender_type")


class Conversation(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "conversations"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(ConversationChannel, nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(200), index=True)
    status: Mapped[str] = mapped_column(String(30), server_default="active")
    # Structured summary only — CLAUDE.md §23: avoid storing raw sensitive
    # conversation content when a summary is sufficient. Full transcripts,
    # if kept at all, belong in Supabase Storage with restricted access.
    summary: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Message(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    direction: Mapped[str] = mapped_column(MessageDirection, nullable=False)
    sender_type: Mapped[str] = mapped_column(MessageSenderType, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String(100))
    # Named message_metadata on the Python side only — `metadata` collides
    # with SQLAlchemy's own Base.metadata attribute. The DB column is named
    # `metadata`, matching CLAUDE.md §8.
    message_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)
    external_id: Mapped[str | None] = mapped_column(String(200), index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
