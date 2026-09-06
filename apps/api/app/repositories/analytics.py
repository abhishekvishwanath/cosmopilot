"""
Aggregate queries for the Phase 11 funnel dashboard (CLAUDE.md §22). Builds
entirely on data already written elsewhere — the `events` table's
`lead_status_changed` history in particular (see events.py's docstring:
"analytics never has to reconstruct history from other tables") — rather
than adding new instrumentation.
"""

import uuid

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.catalog import Treatment
from app.models.event import Event
from app.models.lead import Lead

_BOOKED_APPOINTMENT_STATUSES = ("booked", "confirmed", "completed")


async def count_leads_by_source(db: AsyncSession, clinic_id: uuid.UUID) -> dict[str, int]:
    source_expr = func.coalesce(Lead.source, "unknown")
    query = (
        select(source_expr, func.count())
        .where(Lead.clinic_id == clinic_id)
        .group_by(source_expr)
    )
    result = await db.execute(query)
    return {source: count for source, count in result.all()}


async def count_booked_appointments_by_source(
    db: AsyncSession, clinic_id: uuid.UUID
) -> dict[str, int]:
    source_expr = func.coalesce(Lead.source, "unknown")
    query = (
        select(source_expr, func.count(Appointment.id))
        .select_from(Appointment)
        .join(Lead, Lead.id == Appointment.lead_id)
        .where(
            Appointment.clinic_id == clinic_id,
            Appointment.status.in_(_BOOKED_APPOINTMENT_STATUSES),
        )
        .group_by(source_expr)
    )
    result = await db.execute(query)
    return {source: count for source, count in result.all()}


async def count_booked_appointments_by_treatment(
    db: AsyncSession, clinic_id: uuid.UUID
) -> dict[str, int]:
    name_expr = func.coalesce(Treatment.name, "unspecified")
    query = (
        select(name_expr, func.count(Appointment.id))
        .select_from(Appointment)
        .outerjoin(Treatment, Treatment.id == Appointment.treatment_id)
        .where(
            Appointment.clinic_id == clinic_id,
            Appointment.status.in_(_BOOKED_APPOINTMENT_STATUSES),
        )
        .group_by(name_expr)
    )
    result = await db.execute(query)
    return {name: count for name, count in result.all()}


async def count_leads_ever_reached_status(
    db: AsyncSession, clinic_id: uuid.UUID, status: str
) -> int:
    """
    Distinct leads whose event history shows a `lead_status_changed` ->
    `status` transition at some point — deliberately history-based rather
    than "current status == X", since a lead can pass through e.g.
    QUALIFIED and later move on to BOOKED or even LOST; the current status
    alone would undercount how many leads ever reached that milestone.
    """
    query = select(func.count(distinct(Event.lead_id))).where(
        Event.clinic_id == clinic_id,
        Event.event_type == "lead_status_changed",
        Event.event_metadata["to"].astext == status,
    )
    result = await db.execute(query)
    return result.scalar_one()


async def count_events(
    db: AsyncSession, clinic_id: uuid.UUID, event_type: str, outcome: str | None = None
) -> int:
    """Count events of a given type, optionally filtered by a
    `metadata.outcome` value (e.g. ai_call_ended's "CONTACTED"/"NO_ANSWER")."""
    query = select(func.count()).where(
        Event.clinic_id == clinic_id, Event.event_type == event_type
    )
    if outcome is not None:
        query = query.where(Event.event_metadata["outcome"].astext == outcome)
    result = await db.execute(query)
    return result.scalar_one()


async def count_leads_recovered_via_whatsapp(db: AsyncSession, clinic_id: uuid.UUID) -> int:
    """
    Leads that received a WhatsApp follow-up (CLAUDE.md §16) and later
    reached at least QUALIFIED — the recovery signal CLAUDE.md §22 calls
    "WhatsApp recovery rate". History-based for the same reason as
    count_leads_ever_reached_status: a recovered lead may have since moved
    past QUALIFIED to BOOKED/ATTENDED.
    """
    followed_up = select(Event.lead_id).where(
        Event.clinic_id == clinic_id,
        Event.event_type == "lead_status_changed",
        Event.event_metadata["to"].astext == "WHATSAPP_FOLLOWUP",
    )
    query = select(func.count(distinct(Event.lead_id))).where(
        Event.clinic_id == clinic_id,
        Event.event_type == "lead_status_changed",
        Event.event_metadata["to"].astext.in_(
            ("QUALIFIED", "APPOINTMENT_INTENT", "BOOKED", "CONFIRMED", "ATTENDED")
        ),
        Event.lead_id.in_(followed_up),
    )
    result = await db.execute(query)
    return result.scalar_one()


async def count_appointments_by_terminal_status(
    db: AsyncSession, clinic_id: uuid.UUID, status: str
) -> int:
    query = select(func.count()).where(
        Appointment.clinic_id == clinic_id, Appointment.status == status
    )
    result = await db.execute(query)
    return result.scalar_one()
