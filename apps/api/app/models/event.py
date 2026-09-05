import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPkMixin


class Event(Base, UUIDPkMixin):
    """
    Generic funnel/analytics event log (CLAUDE.md §22). Every funnel-stage
    transition writes here in addition to any entity-specific state change,
    so analytics never has to reconstruct history from other tables.
    Append-only — no updated_at.
    """

    __tablename__ = "events"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), index=True
    )
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[str | None] = mapped_column(String(100))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    event_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)
    # func.now() renders as the SQL function call `now()`, re-evaluated on
    # every insert — a bare string default like "now()" gets frozen by
    # Postgres into a constant at DDL time instead (a well-known gotcha).
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
