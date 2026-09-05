import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Doctor, Treatment


async def list_doctors(db: AsyncSession, clinic_id: uuid.UUID) -> list[Doctor]:
    result = await db.execute(select(Doctor).where(Doctor.clinic_id == clinic_id))
    return list(result.scalars().all())


async def list_active_doctors(db: AsyncSession, clinic_id: uuid.UUID) -> list[Doctor]:
    result = await db.execute(
        select(Doctor).where(Doctor.clinic_id == clinic_id, Doctor.status == "active")
    )
    return list(result.scalars().all())


async def get_doctor(db: AsyncSession, clinic_id: uuid.UUID, doctor_id: uuid.UUID) -> Doctor | None:
    result = await db.execute(
        select(Doctor).where(Doctor.id == doctor_id, Doctor.clinic_id == clinic_id)
    )
    return result.scalars().first()


async def create_doctor(db: AsyncSession, clinic_id: uuid.UUID, data: dict) -> Doctor:
    doctor = Doctor(clinic_id=clinic_id, **data)
    db.add(doctor)
    await db.flush()
    return doctor


async def update_doctor(db: AsyncSession, doctor: Doctor, data: dict) -> Doctor:
    for field, value in data.items():
        setattr(doctor, field, value)
    await db.flush()
    return doctor


async def list_treatments(db: AsyncSession, clinic_id: uuid.UUID) -> list[Treatment]:
    result = await db.execute(select(Treatment).where(Treatment.clinic_id == clinic_id))
    return list(result.scalars().all())


async def list_active_treatments(db: AsyncSession, clinic_id: uuid.UUID) -> list[Treatment]:
    result = await db.execute(
        select(Treatment).where(Treatment.clinic_id == clinic_id, Treatment.status == "active")
    )
    return list(result.scalars().all())


async def get_treatment(
    db: AsyncSession, clinic_id: uuid.UUID, treatment_id: uuid.UUID
) -> Treatment | None:
    result = await db.execute(
        select(Treatment).where(Treatment.id == treatment_id, Treatment.clinic_id == clinic_id)
    )
    return result.scalars().first()


async def create_treatment(db: AsyncSession, clinic_id: uuid.UUID, data: dict) -> Treatment:
    treatment = Treatment(clinic_id=clinic_id, **data)
    db.add(treatment)
    await db.flush()
    return treatment


async def update_treatment(db: AsyncSession, treatment: Treatment, data: dict) -> Treatment:
    for field, value in data.items():
        setattr(treatment, field, value)
    await db.flush()
    return treatment
