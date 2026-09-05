import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPkMixin


class Clinic(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "clinics"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(500))
    primary_phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(320))
    timezone: Mapped[str] = mapped_column(String(50), server_default="Asia/Dubai")
    status: Mapped[str] = mapped_column(String(20), server_default="onboarding")
    settings: Mapped[dict] = mapped_column(JSONB, server_default="{}")


class ClinicLocation(Base, UUIDPkMixin, TimestampMixin):
    __tablename__ = "clinic_locations"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    address: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(120))
    country: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(50))
    opening_hours: Mapped[dict | None] = mapped_column(JSONB)
    timezone: Mapped[str | None] = mapped_column(String(50))


class ClinicStaff(Base, UUIDPkMixin, TimestampMixin):
    """
    Maps a Supabase Auth user (auth.uid()) to a clinic, with a role. This is
    the join the security foundation from Phase 1 needed — CLAUDE.md's data
    model doesn't name it explicitly, but clinic-scoped authorization
    (§23) is impossible without it.
    """

    __tablename__ = "clinic_staff"
    __table_args__ = (
        {
            "comment": (
                "user_id references auth.users (Supabase's own schema, in the "
                "same Postgres instance) — deleting the auth user cascades here."
            )
        },
    )

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Not wrapped in SQLAlchemy's ForeignKey() — the ORM mapper can't resolve
    # a reference to auth.users without a model for it, and we don't own
    # that schema. The real DB-level FK + ON DELETE CASCADE constraint still
    # exists (see the migration) and is what actually enforces this.
    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(20), server_default="staff")
