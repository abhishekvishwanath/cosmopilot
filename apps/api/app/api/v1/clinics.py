import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ClinicPrincipal, get_current_clinic_staff
from app.db.session import get_db
from app.repositories import clinics as clinics_repo
from app.schemas.clinic import (
    ClinicLocationCreate,
    ClinicLocationRead,
    ClinicLocationUpdate,
    ClinicRead,
    ClinicUpdate,
)

router = APIRouter(prefix="/clinics", tags=["clinics"])


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": {"code": "not_found", "message": "Not found.", "details": {}}},
    )


@router.get("/me", response_model=ClinicRead)
async def get_my_clinic(
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicRead:
    clinic = await clinics_repo.get_clinic(db, principal.clinic_id)
    if clinic is None:
        raise _not_found()
    return ClinicRead.model_validate(clinic)


@router.patch("/me", response_model=ClinicRead)
async def update_my_clinic(
    payload: ClinicUpdate,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicRead:
    clinic = await clinics_repo.get_clinic(db, principal.clinic_id)
    if clinic is None:
        raise _not_found()
    updated = await clinics_repo.update_clinic(
        db, clinic, payload.model_dump(exclude_unset=True)
    )
    await db.commit()
    return ClinicRead.model_validate(updated)


@router.get("/me/locations", response_model=list[ClinicLocationRead])
async def list_my_locations(
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ClinicLocationRead]:
    locations = await clinics_repo.list_locations(db, principal.clinic_id)
    return [ClinicLocationRead.model_validate(loc) for loc in locations]


@router.post(
    "/me/locations", response_model=ClinicLocationRead, status_code=status.HTTP_201_CREATED
)
async def create_my_location(
    payload: ClinicLocationCreate,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicLocationRead:
    location = await clinics_repo.create_location(
        db, principal.clinic_id, payload.model_dump()
    )
    await db.commit()
    return ClinicLocationRead.model_validate(location)


@router.patch("/me/locations/{location_id}", response_model=ClinicLocationRead)
async def update_my_location(
    location_id: uuid.UUID,
    payload: ClinicLocationUpdate,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicLocationRead:
    location = await clinics_repo.get_location(db, principal.clinic_id, location_id)
    if location is None:
        raise _not_found()
    updated = await clinics_repo.update_location(
        db, location, payload.model_dump(exclude_unset=True)
    )
    await db.commit()
    return ClinicLocationRead.model_validate(updated)
