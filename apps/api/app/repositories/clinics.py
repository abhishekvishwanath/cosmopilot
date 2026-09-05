import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import Clinic, ClinicLocation


async def get_clinic(db: AsyncSession, clinic_id: uuid.UUID) -> Clinic | None:
    return await db.get(Clinic, clinic_id)


async def update_clinic(db: AsyncSession, clinic: Clinic, data: dict) -> Clinic:
    for field, value in data.items():
        setattr(clinic, field, value)
    await db.flush()
    return clinic


async def list_locations(db: AsyncSession, clinic_id: uuid.UUID) -> list[ClinicLocation]:
    result = await db.execute(
        select(ClinicLocation).where(ClinicLocation.clinic_id == clinic_id)
    )
    return list(result.scalars().all())


async def create_location(
    db: AsyncSession, clinic_id: uuid.UUID, data: dict
) -> ClinicLocation:
    location = ClinicLocation(clinic_id=clinic_id, **data)
    db.add(location)
    await db.flush()
    return location


async def get_location(
    db: AsyncSession, clinic_id: uuid.UUID, location_id: uuid.UUID
) -> ClinicLocation | None:
    result = await db.execute(
        select(ClinicLocation).where(
            ClinicLocation.id == location_id, ClinicLocation.clinic_id == clinic_id
        )
    )
    return result.scalars().first()


async def update_location(db: AsyncSession, location: ClinicLocation, data: dict) -> ClinicLocation:
    for field, value in data.items():
        setattr(location, field, value)
    await db.flush()
    return location
