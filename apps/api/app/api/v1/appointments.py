import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ClinicPrincipal, get_current_clinic_staff
from app.db.session import get_db
from app.models.appointment import Appointment
from app.repositories import appointments as appointments_repo
from app.repositories import leads as leads_repo
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentEventRead,
    AppointmentRead,
    AppointmentStatusUpdate,
    AppointmentUpdate,
)
from app.services import appointments as appointments_service

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _not_found(message: str = "Appointment not found.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": {"code": "not_found", "message": message, "details": {}}},
    )


async def _get_appointment_or_404(
    db: AsyncSession, clinic_id: uuid.UUID, appointment_id: uuid.UUID
) -> Appointment:
    appointment = await appointments_repo.get_appointment(db, clinic_id, appointment_id)
    if appointment is None:
        raise _not_found()
    return appointment


@router.get("", response_model=list[AppointmentRead])
async def list_appointments(
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
    lead_id: Annotated[uuid.UUID | None, Query()] = None,
    upcoming: Annotated[bool, Query()] = False,
) -> list[AppointmentRead]:
    appointments = await appointments_repo.list_appointments(
        db, principal.clinic_id, lead_id=lead_id, upcoming_only=upcoming
    )
    return [AppointmentRead.model_validate(a) for a in appointments]


@router.post("", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    payload: AppointmentCreate,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentRead:
    lead = await leads_repo.get_lead(db, principal.clinic_id, payload.lead_id)
    if lead is None:
        raise _not_found("Lead not found.")

    appointment = await appointments_service.create_appointment(
        db, principal.clinic_id, payload.model_dump()
    )
    await db.commit()
    return AppointmentRead.model_validate(appointment)


@router.get("/{appointment_id}", response_model=AppointmentRead)
async def get_appointment(
    appointment_id: uuid.UUID,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentRead:
    appointment = await _get_appointment_or_404(db, principal.clinic_id, appointment_id)
    return AppointmentRead.model_validate(appointment)


@router.patch("/{appointment_id}", response_model=AppointmentRead)
async def update_appointment(
    appointment_id: uuid.UUID,
    payload: AppointmentUpdate,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentRead:
    appointment = await _get_appointment_or_404(db, principal.clinic_id, appointment_id)
    updated = await appointments_repo.update_appointment(
        db, appointment, payload.model_dump(exclude_unset=True)
    )
    await db.commit()
    return AppointmentRead.model_validate(updated)


@router.post("/{appointment_id}/status", response_model=AppointmentRead)
async def update_appointment_status(
    appointment_id: uuid.UUID,
    payload: AppointmentStatusUpdate,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AppointmentRead:
    appointment = await _get_appointment_or_404(db, principal.clinic_id, appointment_id)
    lead = await leads_repo.get_lead(db, principal.clinic_id, appointment.lead_id)
    if lead is None:
        raise _not_found("Lead not found.")

    updated = await appointments_service.transition_appointment_status(
        db, appointment, payload.status, lead, reason=payload.reason
    )
    await db.commit()
    return AppointmentRead.model_validate(updated)


@router.get("/{appointment_id}/events", response_model=list[AppointmentEventRead])
async def get_appointment_events(
    appointment_id: uuid.UUID,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AppointmentEventRead]:
    await _get_appointment_or_404(db, principal.clinic_id, appointment_id)
    events = await appointments_repo.list_appointment_events(db, appointment_id)
    return [AppointmentEventRead.model_validate(e) for e in events]
