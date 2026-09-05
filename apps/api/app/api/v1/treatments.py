import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ClinicPrincipal, get_current_clinic_staff
from app.db.session import get_db
from app.repositories import catalog as catalog_repo
from app.schemas.catalog import TreatmentCreate, TreatmentRead, TreatmentUpdate

router = APIRouter(prefix="/treatments", tags=["treatments"])


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": {"code": "not_found", "message": "Treatment not found.", "details": {}}},
    )


@router.get("", response_model=list[TreatmentRead])
async def list_treatments(
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[TreatmentRead]:
    treatments = await catalog_repo.list_treatments(db, principal.clinic_id)
    return [TreatmentRead.model_validate(t) for t in treatments]


@router.post("", response_model=TreatmentRead, status_code=status.HTTP_201_CREATED)
async def create_treatment(
    payload: TreatmentCreate,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TreatmentRead:
    treatment = await catalog_repo.create_treatment(
        db, principal.clinic_id, payload.model_dump()
    )
    await db.commit()
    return TreatmentRead.model_validate(treatment)


@router.get("/{treatment_id}", response_model=TreatmentRead)
async def get_treatment(
    treatment_id: uuid.UUID,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TreatmentRead:
    treatment = await catalog_repo.get_treatment(db, principal.clinic_id, treatment_id)
    if treatment is None:
        raise _not_found()
    return TreatmentRead.model_validate(treatment)


@router.patch("/{treatment_id}", response_model=TreatmentRead)
async def update_treatment(
    treatment_id: uuid.UUID,
    payload: TreatmentUpdate,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TreatmentRead:
    treatment = await catalog_repo.get_treatment(db, principal.clinic_id, treatment_id)
    if treatment is None:
        raise _not_found()
    updated = await catalog_repo.update_treatment(
        db, treatment, payload.model_dump(exclude_unset=True)
    )
    await db.commit()
    return TreatmentRead.model_validate(updated)
