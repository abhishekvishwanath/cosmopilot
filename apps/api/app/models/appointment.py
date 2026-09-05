import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPkMixin

AppointmentStatus = Enum(
    "pending", "booked", "confirmed", "cancelled", "completed", "no_show",
    name="appointment_status",
)


class Appointment(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "appointments"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    doctor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("doctors.id", ondelete="SET NULL"), index=True
    )
    treatment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("treatments.id", ondelete="SET NULL"), index=True
    )
    # ID from the CalendarProvider in use (MockCalendarProvider for now,
    # Phase 7) — this is what keeps the provider swappable without touching
    # this table. Not populated until Phase 7 builds the appointment engine;
    # Phase 2 seed data leaves this null.
    external_id: Mapped[str | None] = mapped_column(String(200), index=True)
    start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(AppointmentStatus, server_default="pending", index=True)
    location: Mapped[str | None] = mapped_column(String(300))


class AppointmentEvent(Base, UUIDPkMixin):
    """Append-only audit trail — powers the CRM lead timeline (CLAUDE.md §19)."""

    __tablename__ = "appointment_events"

    appointment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
