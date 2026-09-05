import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPkMixin

# CLAUDE.md §9 — the lead state machine. Enforced as a real Postgres enum so
# an invalid transition can't be written by anything other than the service
# layer that validates it, not just convention.
LEAD_STATUSES = (
    "NEW",
    "CONTACTING",
    "CONTACTED",
    "QUALIFIED",
    "APPOINTMENT_INTENT",
    "BOOKED",
    "CONFIRMED",
    "ATTENDED",
    "NO_ANSWER",
    "WHATSAPP_FOLLOWUP",
    "HUMAN_REQUIRED",
    "CANCELLED",
    "NO_SHOW",
    "LOST",
    "REACTIVATION",
)

LeadStatus = Enum(*LEAD_STATUSES, name="lead_status")


class Lead(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "leads"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(50))
    whatsapp: Mapped[str | None] = mapped_column(String(50))
    treatment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("treatments.id", ondelete="SET NULL"), index=True
    )
    source: Mapped[str | None] = mapped_column(String(100))
    landing_page: Mapped[str | None] = mapped_column(String(500))
    preferred_time: Mapped[str | None] = mapped_column(String(200))
    intent_score: Mapped[int | None] = mapped_column()
    consent: Mapped[bool] = mapped_column(Boolean, server_default="false")
    status: Mapped[str] = mapped_column(LeadStatus, server_default="NEW", index=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column()


class Consent(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "consents"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    consent_type: Mapped[str] = mapped_column(String(50), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    source: Mapped[str | None] = mapped_column(Text)
