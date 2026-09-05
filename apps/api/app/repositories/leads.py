import uuid
from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead


async def list_leads(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    status: str | None = None,
    limit: int = 50,
    after: tuple[datetime, uuid.UUID] | None = None,
) -> list[Lead]:
    query = select(Lead).where(Lead.clinic_id == clinic_id)
    if status:
        query = query.where(Lead.status == status)
    if after:
        after_created_at, after_id = after
        query = query.where(
            or_(
                Lead.created_at < after_created_at,
                and_(Lead.created_at == after_created_at, Lead.id < after_id),
            )
        )
    query = query.order_by(Lead.created_at.desc(), Lead.id.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_lead(db: AsyncSession, clinic_id: uuid.UUID, lead_id: uuid.UUID) -> Lead | None:
    result = await db.execute(select(Lead).where(Lead.id == lead_id, Lead.clinic_id == clinic_id))
    return result.scalars().first()


async def create_lead(db: AsyncSession, clinic_id: uuid.UUID, data: dict) -> Lead:
    lead = Lead(clinic_id=clinic_id, **data)
    db.add(lead)
    await db.flush()
    return lead


async def update_lead(db: AsyncSession, lead: Lead, data: dict) -> Lead:
    for field, value in data.items():
        setattr(lead, field, value)
    await db.flush()
    return lead


async def count_by_status(db: AsyncSession, clinic_id: uuid.UUID) -> dict[str, int]:
    query = (
        select(Lead.status, func.count())
        .where(Lead.clinic_id == clinic_id)
        .group_by(Lead.status)
    )
    result = await db.execute(query)
    return {status: count for status, count in result.all()}
