import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import concierge as concierge_agent
from app.core.logging import log_with_fields
from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.models.catalog import Doctor, Treatment
from app.providers.llm.base import LLMProviderError
from app.repositories import catalog as catalog_repo
from app.repositories import clinics as clinics_repo
from app.repositories import leads as leads_repo
from app.repositories import visitor_sessions as visitor_sessions_repo
from app.schemas.concierge import (
    ConciergeMessageResponse,
    PublicConciergeMessageRequest,
    ToolCallRead,
)
from app.schemas.public import (
    PublicClinicRead,
    PublicDoctorRead,
    PublicLeadCreate,
    PublicLeadRead,
    PublicLocationRead,
    PublicTreatmentRead,
)
from app.services import leads as leads_service
from app.services import notifications as notifications_service
from app.services.n8n import notify_lead_created
from app.utils.slugify import slugify
from app.utils.validation import has_min_digits

logger = logging.getLogger("cosmopilot.public.concierge")

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


def _validation_error(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"error": {"code": code, "message": message, "details": {}}},
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


# Enquiry-form submissions are higher-value spam/abuse targets than a read
# endpoint — a tighter limit than the router-wide 60/min applies on top of
# it (both dependencies run; whichever trips first wins).
@router.post(
    "/leads",
    response_model=PublicLeadRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(max_requests=5, window_seconds=600))],
)
async def create_public_lead(
    payload: PublicLeadCreate, db: Annotated[AsyncSession, Depends(get_db)]
) -> PublicLeadRead:
    if not payload.consent:
        raise _validation_error(
            "consent_required", "Consent is required so we can contact you about your enquiry."
        )
    if not has_min_digits(payload.phone, 7):
        raise _validation_error("invalid_phone", "Please enter a valid phone number.")

    clinic = await clinics_repo.get_active_clinic(db)
    if clinic is None:
        raise _not_found("Clinic")

    treatment: Treatment | None = None
    if payload.treatment_id is not None:
        treatment = await catalog_repo.get_treatment(db, clinic.id, payload.treatment_id)
        if treatment is None or treatment.status != "active":
            raise _validation_error(
                "invalid_treatment", "The selected treatment is not currently available."
            )

    lead = await leads_service.create_lead(
        db,
        clinic.id,
        {
            "name": payload.name.strip(),
            "phone": payload.phone.strip(),
            "email": payload.email,
            "whatsapp": payload.phone.strip() if payload.contact_method == "WhatsApp" else None,
            "treatment_id": treatment.id if treatment else None,
            "source": payload.source or "website",
            "landing_page": payload.landing_page,
            "preferred_time": payload.preferred_time,
            "consent": True,
        },
        event_metadata={
            "contact_method": payload.contact_method,
            "campaign": payload.campaign,
            "anonymous_id": payload.anonymous_id,
        },
    )

    await visitor_sessions_repo.create_visitor_session(
        db,
        clinic_id=clinic.id,
        treatment_id=treatment.id if treatment else None,
        source=payload.source,
        campaign=payload.campaign,
        landing_page=payload.landing_page,
        anonymous_id=payload.anonymous_id,
    )

    await notifications_service.notify_clinic_of_new_lead(
        db, clinic, lead, treatment.name if treatment else None
    )

    await db.commit()
    # CLAUDE.md §13/§14 — this is what actually starts the ~60-second
    # automated response promise: n8n's "new lead" workflow picks this up
    # and triggers the AI contact attempt (CLAUDE.md §17 Workflow A).
    await notify_lead_created(lead.id, clinic.id)
    return PublicLeadRead(id=lead.id, status=lead.status)


# The web-chat AI Concierge — CLAUDE.md Phase 6. Requires an existing
# lead_id (from a prior /public/leads submission) rather than starting
# fully anonymous: Conversation.lead_id is NOT NULL by design (Phase 2),
# and CLAUDE.md's own flow (§4) has "Lead Created" happen before "AI
# Concierge <60 sec" contact — the concierge follows up on an enquiry,
# it doesn't cold-open one. A generous-but-bounded limit (this is a real
# conversation, not a one-shot form) protects the local LLM from abuse.
@router.post(
    "/concierge/messages",
    response_model=ConciergeMessageResponse,
    dependencies=[Depends(rate_limit(max_requests=20, window_seconds=600))],
)
async def send_public_concierge_message(
    payload: PublicConciergeMessageRequest, db: Annotated[AsyncSession, Depends(get_db)]
) -> ConciergeMessageResponse:
    clinic = await clinics_repo.get_active_clinic(db)
    if clinic is None:
        raise _not_found("Clinic")

    lead = await leads_repo.get_lead(db, clinic.id, payload.lead_id)
    if lead is None:
        raise _not_found("Lead")

    try:
        conversation = await concierge_agent.get_or_create_conversation(
            db, clinic.id, lead.id, payload.conversation_id
        )
    except concierge_agent.ConversationMismatchError as exc:
        raise _not_found(str(exc)) from exc

    result = await concierge_agent.handle_turn(db, clinic, lead, conversation, payload.message)
    await db.commit()

    try:
        await concierge_agent.summarize_conversation(db, conversation)
        await db.commit()
    except LLMProviderError:
        log_with_fields(
            logger,
            logging.WARNING,
            "summary_generation_failed",
            conversation_id=str(conversation.id),
        )

    return ConciergeMessageResponse(
        conversation_id=result.conversation_id,
        reply=result.reply,
        lead_status=result.lead_status,
        tool_calls=[
            ToolCallRead(name=t.name, arguments=t.arguments, result=t.result)
            for t in result.tool_calls
        ],
    )
