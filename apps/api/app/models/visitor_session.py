import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPkMixin


class VisitorSession(Base, UUIDPkMixin):
    """
    Attribution snapshot captured at lead-creation time (CLAUDE.md §8, §21)
    — not full page-view analytics (that's a Phase 11 concern). One row per
    enquiry, correlating the visitor's anonymous_id with source, campaign,
    landing page, and treatment interest. Append-only — no updated_at.
    """

    __tablename__ = "visitor_sessions"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    treatment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("treatments.id", ondelete="SET NULL"), index=True
    )
    source: Mapped[str | None] = mapped_column(String(100))
    campaign: Mapped[str | None] = mapped_column(String(200))
    landing_page: Mapped[str | None] = mapped_column(String(500))
    anonymous_id: Mapped[str | None] = mapped_column(String(100), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
