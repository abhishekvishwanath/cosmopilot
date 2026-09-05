from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.models.catalog import Doctor, Treatment
from app.repositories import catalog as catalog_repo
from app.repositories import clinics as clinics_repo
from app.schemas.public import (
    PublicClinicRead,
    PublicDoctorRead,
    PublicLocationRead,
    PublicTreatmentRead,
)
from app.utils.slugify import slugify

# Unauthenticated by design — this is what the marketing site renders for
# anonymous visitors (CLAUDE.md §28: minimal, rate-limited, never leaks
# clinic-internal or patient data). Every route here returns only fields a
# visitor is meant to see.
router = APIRouter(
    prefix="/public",
    tags=["public"],
    dependencies=[Depends(rate_limit(max_requests=60, window_seconds=60))],
)


def _not_found(what: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": {"code": "not_found", "message": f"{what} not found.", "details": {}}},
    )


def _doctor_to_public(doctor: Doctor) -> PublicDoctorRead:
    return PublicDoctorRead(
        id=doctor.id,
        slug=slugify(doctor.name),
        name=doctor.name,
        title=doctor.title,
        specialties=doctor.specialties,
        credentials=doctor.credentials,
        bio=doctor.bio,
        photo_url=doctor.photo_url,
    )


def _treatment_to_public(treatment: Treatment) -> PublicTreatmentRead:
    return PublicTreatmentRead(
        id=treatment.id,
        slug=slugify(treatment.name),
        name=treatment.name,
        category=treatment.category,
        description=treatment.description,
        approved_information=treatment.approved_information,
        faq=treatment.faq,
        price_guidance=treatment.price_guidance,
        duration=treatment.duration,
        booking_enabled=treatment.booking_enabled,
    )


@router.get("/clinic", response_model=PublicClinicRead)
async def get_public_clinic(db: Annotated[AsyncSession, Depends(get_db)]) -> PublicClinicRead:
    clinic = await clinics_repo.get_active_clinic(db)
    if clinic is None:
        raise _not_found("Clinic")
    locations = await clinics_repo.list_locations(db, clinic.id)
    return PublicClinicRead(
        id=clinic.id,
        name=clinic.name,
        description=clinic.description,
        website=clinic.website,
        primary_phone=clinic.primary_phone,
        email=clinic.email,
        timezone=clinic.timezone,
        locations=[PublicLocationRead.model_validate(loc) for loc in locations],
    )


@router.get("/doctors", response_model=list[PublicDoctorRead])
async def list_public_doctors(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PublicDoctorRead]:
    clinic = await clinics_repo.get_active_clinic(db)
    if clinic is None:
        return []
    doctors = await catalog_repo.list_active_doctors(db, clinic.id)
    return [_doctor_to_public(d) for d in doctors]


@router.get("/doctors/{slug}", response_model=PublicDoctorRead)
async def get_public_doctor(
    slug: str, db: Annotated[AsyncSession, Depends(get_db)]
) -> PublicDoctorRead:
    clinic = await clinics_repo.get_active_clinic(db)
    if clinic is not None:
        doctors = await catalog_repo.list_active_doctors(db, clinic.id)
        for doctor in doctors:
            if slugify(doctor.name) == slug:
                return _doctor_to_public(doctor)
    raise _not_found("Doctor")


@router.get("/treatments", response_model=list[PublicTreatmentRead])
async def list_public_treatments(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PublicTreatmentRead]:
    clinic = await clinics_repo.get_active_clinic(db)
    if clinic is None:
        return []
    treatments = await catalog_repo.list_active_treatments(db, clinic.id)
    return [_treatment_to_public(t) for t in treatments]


@router.get("/treatments/{slug}", response_model=PublicTreatmentRead)
async def get_public_treatment(
    slug: str, db: Annotated[AsyncSession, Depends(get_db)]
) -> PublicTreatmentRead:
    clinic = await clinics_repo.get_active_clinic(db)
    if clinic is not None:
        treatments = await catalog_repo.list_active_treatments(db, clinic.id)
        for treatment in treatments:
            if slugify(treatment.name) == slug:
                return _treatment_to_public(treatment)
    raise _not_found("Treatment")
