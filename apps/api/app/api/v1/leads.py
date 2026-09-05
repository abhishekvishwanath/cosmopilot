import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ClinicPrincipal, get_current_clinic_staff
from app.db.session import get_db
from app.models.lead import Lead
from app.repositories import events as events_repo
from app.repositories import leads as leads_repo
from app.schemas.event import EventRead
from app.schemas.lead import LeadCreate, LeadPage, LeadRead, LeadStatusUpdate, LeadUpdate
from app.services import leads as leads_service
from app.utils.pagination import decode_cursor, encode_cursor

router = APIRouter(prefix="/leads", tags=["leads"])


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": {"code": "not_found", "message": "Lead not found.", "details": {}}},
    )


async def _get_lead_or_404(db: AsyncSession, clinic_id: uuid.UUID, lead_id: uuid.UUID) -> Lead:
    lead = await leads_repo.get_lead(db, clinic_id, lead_id)
    if lead is None:
        raise _not_found()
    return lead


@router.get("", response_model=LeadPage)
async def list_leads(
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> LeadPage:
    after = decode_cursor(cursor) if cursor else None
    leads = await leads_repo.list_leads(
        db, principal.clinic_id, status=status_filter, limit=limit, after=after
    )
    next_cursor = (
        encode_cursor(leads[-1].created_at, leads[-1].id) if len(leads) == limit else None
    )
    items = [LeadRead.model_validate(lead) for lead in leads]
    return LeadPage(items=items, next_cursor=next_cursor)


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
async def create_lead(
    payload: LeadCreate,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LeadRead:
    # Manually-entered lead (CRM staff use). The public, unauthenticated
    # enquiry-form intake endpoint — with rate limiting, attribution, and
    # visitor-session stitching — is a Phase 4 (Lead Capture) deliverable.
    lead = await leads_service.create_lead(db, principal.clinic_id, payload.model_dump())
    await db.commit()
    return LeadRead.model_validate(lead)


@router.get("/{lead_id}", response_model=LeadRead)
async def get_lead(
    lead_id: uuid.UUID,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LeadRead:
    lead = await _get_lead_or_404(db, principal.clinic_id, lead_id)
    return LeadRead.model_validate(lead)


@router.patch("/{lead_id}", response_model=LeadRead)
async def update_lead(
    lead_id: uuid.UUID,
    payload: LeadUpdate,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LeadRead:
    lead = await _get_lead_or_404(db, principal.clinic_id, lead_id)
    updated = await leads_repo.update_lead(db, lead, payload.model_dump(exclude_unset=True))
    await db.commit()
    return LeadRead.model_validate(updated)


@router.post("/{lead_id}/status", response_model=LeadRead)
async def update_lead_status(
    lead_id: uuid.UUID,
    payload: LeadStatusUpdate,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LeadRead:
    lead = await _get_lead_or_404(db, principal.clinic_id, lead_id)
    updated = await leads_service.transition_lead_status(db, lead, payload.status)
    await db.commit()
    return LeadRead.model_validate(updated)


@router.get("/{lead_id}/timeline", response_model=list[EventRead])
async def get_lead_timeline(
    lead_id: uuid.UUID,
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[EventRead]:
    await _get_lead_or_404(db, principal.clinic_id, lead_id)
    events = await events_repo.list_events(db, principal.clinic_id, lead_id=lead_id)
    return [EventRead.model_validate(event) for event in reversed(events)]
