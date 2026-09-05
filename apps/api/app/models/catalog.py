import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPkMixin


class Doctor(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "doctors"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    specialties: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    credentials: Mapped[str | None] = mapped_column(Text)
    bio: Mapped[str | None] = mapped_column(Text)
    photo_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), server_default="active")


class Treatment(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "treatments"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    # Only source of truth the AI concierge may quote from (CLAUDE.md §11) —
    # never invented, never derived from general model knowledge.
    approved_information: Mapped[str | None] = mapped_column(Text)
    faq: Mapped[list[dict] | None] = mapped_column(JSONB)
    price_guidance: Mapped[str | None] = mapped_column(Text)
    duration: Mapped[str | None] = mapped_column(String(100))
    booking_enabled: Mapped[bool] = mapped_column(server_default="true")
    status: Mapped[str] = mapped_column(String(20), server_default="active")
