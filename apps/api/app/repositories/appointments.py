import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment, AppointmentEvent


async def list_appointments(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    lead_id: uuid.UUID | None = None,
    upcoming_only: bool = False,
    limit: int = 50,
) -> list[Appointment]:
    query = select(Appointment).where(Appointment.clinic_id == clinic_id)
    if lead_id:
        query = query.where(Appointment.lead_id == lead_id)
    if upcoming_only:
        query = query.where(Appointment.start >= func.now())
    query = query.order_by(Appointment.start.asc().nulls_last()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_appointment(
    db: AsyncSession, clinic_id: uuid.UUID, appointment_id: uuid.UUID
) -> Appointment | None:
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == appointment_id, Appointment.clinic_id == clinic_id
        )
    )
    return result.scalars().first()


async def create_appointment(db: AsyncSession, clinic_id: uuid.UUID, data: dict) -> Appointment:
    appointment = Appointment(clinic_id=clinic_id, **data)
    db.add(appointment)
    await db.flush()
    return appointment


async def update_appointment(
    db: AsyncSession, appointment: Appointment, data: dict
) -> Appointment:
    for field, value in data.items():
        setattr(appointment, field, value)
    await db.flush()
    return appointment


async def add_appointment_event(
    db: AsyncSession,
    appointment_id: uuid.UUID,
    event_type: str,
    metadata: dict | None = None,
) -> AppointmentEvent:
    event = AppointmentEvent(
        appointment_id=appointment_id, event_type=event_type, event_metadata=metadata
    )
    db.add(event)
    await db.flush()
    return event


async def list_appointment_events(
    db: AsyncSession, appointment_id: uuid.UUID
) -> list[AppointmentEvent]:
    result = await db.execute(
        select(AppointmentEvent)
        .where(AppointmentEvent.appointment_id == appointment_id)
        .order_by(AppointmentEvent.timestamp.asc())
    )
    return list(result.scalars().all())


async def count_by_status(db: AsyncSession, clinic_id: uuid.UUID) -> dict[str, int]:
    query = (
        select(Appointment.status, func.count())
        .where(Appointment.clinic_id == clinic_id)
        .group_by(Appointment.status)
    )
    result = await db.execute(query)
    return {status: count for status, count in result.all()}


async def count_upcoming(db: AsyncSession, clinic_id: uuid.UUID) -> int:
    query = select(func.count()).where(
        Appointment.clinic_id == clinic_id, Appointment.start >= func.now()
    )
    result = await db.execute(query)
    return result.scalar_one()
