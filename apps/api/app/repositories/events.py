import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event


async def create_event(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    event_type: str,
    source: str | None = None,
    lead_id: uuid.UUID | None = None,
    appointment_id: uuid.UUID | None = None,
    metadata: dict | None = None,
) -> Event:
    event = Event(
        clinic_id=clinic_id,
        lead_id=lead_id,
        appointment_id=appointment_id,
        source=source,
        event_type=event_type,
        event_metadata=metadata,
    )
    db.add(event)
    await db.flush()
    return event


async def list_events(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    lead_id: uuid.UUID | None = None,
    limit: int = 100,
) -> list[Event]:
    query = select(Event).where(Event.clinic_id == clinic_id)
    if lead_id:
        query = query.where(Event.lead_id == lead_id)
    query = query.order_by(Event.timestamp.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
