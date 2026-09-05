import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ClinicPrincipal, get_current_clinic_staff
from app.db.session import get_db
from app.repositories import catalog as catalog_repo
from app.schemas.catalog import DoctorCreate, DoctorRead, DoctorUpdate

router = APIRouter(prefix="/doctors", tags=["doctors"])


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": {"code": "not_found", "message": "Doctor not found.", "details": {}}},
    )


@router.get("", response_model=list[DoctorRead])
async def list_doctors(
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DoctorRead]:
    doctors = await catalog_repo.list_doctors(db, principal.clinic_id)
    return [DoctorRead.model_validate(d) for d in doctors]


@router.post("", response_model=DoctorRead, status_code=status.HTTP_201_CREATED)
async def create_doctor(
    payload: DoctorCreate,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DoctorRead:
    doctor = await catalog_repo.create_doctor(db, principal.clinic_id, payload.model_dump())
    await db.commit()
    return DoctorRead.model_validate(doctor)


@router.get("/{doctor_id}", response_model=DoctorRead)
async def get_doctor(
    doctor_id: uuid.UUID,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DoctorRead:
    doctor = await catalog_repo.get_doctor(db, principal.clinic_id, doctor_id)
    if doctor is None:
        raise _not_found()
    return DoctorRead.model_validate(doctor)


@router.patch("/{doctor_id}", response_model=DoctorRead)
async def update_doctor(
    doctor_id: uuid.UUID,
    payload: DoctorUpdate,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DoctorRead:
    doctor = await catalog_repo.get_doctor(db, principal.clinic_id, doctor_id)
    if doctor is None:
        raise _not_found()
    updated = await catalog_repo.update_doctor(db, doctor, payload.model_dump(exclude_unset=True))
    await db.commit()
    return DoctorRead.model_validate(updated)
