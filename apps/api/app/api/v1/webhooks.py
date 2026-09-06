"""
Inbound actions n8n's workflows call (CLAUDE.md §17/§24, Phase 8).
Authenticated by a shared secret (verify_n8n_webhook), not a staff JWT —
n8n is a trusted automation caller, not a logged-in user. Every
state-changing action here is idempotent on the state it would otherwise
duplicate (CLAUDE.md §24 "never process ... events twice"): re-running the
same n8n step twice (a retried HTTP Request node, a re-triggered workflow)
must never double-contact a patient or double-transition a status.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import log_with_fields
from app.core.rate_limit import rate_limit
from app.core.security import verify_n8n_webhook
from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.lead import Lead
from app.providers.email import get_email_provider
from app.providers.voice import get_voice_provider
from app.providers.voice.base import VoiceProviderError
from app.providers.whatsapp import get_whatsapp_provider
from app.repositories import appointments as appointments_repo
from app.repositories import catalog as catalog_repo
from app.repositories import clinics as clinics_repo
from app.repositories import conversations as conversations_repo
from app.repositories import events as events_repo
from app.repositories import leads as leads_repo
from app.schemas.webhooks import (
    CallAttemptResult,
    LeadStatusRead,
    ReminderCandidate,
    ReminderCandidatesRead,
    WebhookActionResult,
    WhatsAppFollowupResult,
)
from app.services import leads as leads_service

logger = logging.getLogger("cosmopilot.webhooks.n8n")

router = APIRouter(
    prefix="/webhooks/n8n",
    tags=["webhooks"],
    dependencies=[
        Depends(verify_n8n_webhook),
        Depends(rate_limit(max_requests=120, window_seconds=60)),
    ],
)

_ACTIVE_APPOINTMENT_STATUSES = ("pending", "booked", "confirmed")


def _not_found(what: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": {"code": "not_found", "message": f"{what} not found.", "details": {}}},
    )


def _validation_error(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"error": {"code": "validation_error", "message": message, "details": {}}},
    )


async def _get_lead_or_404(db: AsyncSession, clinic_id: uuid.UUID, lead_id: uuid.UUID) -> Lead:
    lead = await leads_repo.get_lead(db, clinic_id, lead_id)
    if lead is None:
        raise _not_found("Lead")
    return lead


async def _get_appointment_or_404(
    db: AsyncSession, clinic_id: uuid.UUID, appointment_id: uuid.UUID
) -> Appointment:
    appointment = await appointments_repo.get_appointment(db, clinic_id, appointment_id)
    if appointment is None:
        raise _not_found("Appointment")
    return appointment


@router.get("/leads/{lead_id}", response_model=LeadStatusRead)
async def get_lead_status(
    lead_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LeadStatusRead:
    lead = await _get_lead_or_404(db, clinic_id, lead_id)
    appointments = await appointments_repo.list_appointments(db, clinic_id, lead_id=lead.id)
    has_active = any(a.status in _ACTIVE_APPOINTMENT_STATUSES for a in appointments)
    return LeadStatusRead(
        lead_id=lead.id,
        status=lead.status,
        name=lead.name,
        phone=lead.phone,
        whatsapp=lead.whatsapp,
        has_active_appointment=has_active,
    )


# Workflow A (CLAUDE.md §17) — n8n calls this right after receiving the
# lead.created push. Idempotent on lead.status: a lead that's already past
# NEW (e.g. this step got retried) is reported back, not re-attempted.
@router.post("/leads/{lead_id}/attempt-call", response_model=CallAttemptResult)
async def attempt_call(
    lead_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CallAttemptResult:
    lead = await _get_lead_or_404(db, clinic_id, lead_id)
    clinic = await clinics_repo.get_clinic(db, clinic_id)
    if clinic is None:
        raise _not_found("Clinic")

    if lead.status != "NEW":
        return CallAttemptResult(
            attempted=False, lead_status=lead.status, reason="lead is no longer NEW"
        )
    if not lead.consent:
        raise _validation_error("Cannot contact a lead without consent on file.")
    if not lead.phone:
        raise _validation_error("Lead has no phone number to call.")

    await leads_service.transition_lead_status(db, lead, "CONTACTING")

    treatment_name = None
    if lead.treatment_id:
        treatment = await catalog_repo.get_treatment(db, clinic_id, lead.treatment_id)
        treatment_name = treatment.name if treatment else None

    provider = get_voice_provider()
    try:
        handle = await provider.start_call(
            to=lead.phone,
            clinic_name=clinic.name,
            lead_name=lead.name,
            clinic_id=clinic_id,
            lead_id=lead.id,
            treatment_name=treatment_name,
        )
    except VoiceProviderError as exc:
        # The call never happened at all (bad number, provider/account
        # limitation, etc) — never fabricate an outcome for it (CLAUDE.md
        # §25); hand off to a human instead of leaving the lead stuck at
        # CONTACTING forever.
        log_with_fields(
            logger, logging.WARNING, "voice_call_failed", lead_id=str(lead.id), error=str(exc)
        )
        await leads_service.transition_lead_status(db, lead, "HUMAN_REQUIRED")
        await events_repo.create_event(
            db,
            clinic_id=clinic_id,
            event_type="ai_call_failed",
            source="n8n",
            lead_id=lead.id,
            metadata={"error": str(exc)},
        )
        await db.commit()
        return CallAttemptResult(
            attempted=False, lead_status="HUMAN_REQUIRED", reason="voice provider call failed"
        )

    await events_repo.create_event(
        db,
        clinic_id=clinic_id,
        event_type="ai_call_attempted",
        source="n8n",
        lead_id=lead.id,
        metadata={"call_id": handle.call_id, "outcome": handle.status},
    )

    if handle.status == "initiated":
        # Real async provider (Vapi) — the actual outcome isn't known yet.
        # It arrives later via Vapi's own end-of-call-report webhook
        # (app/api/v1/vapi.py), which is what transitions the lead to
        # CONTACTED/NO_ANSWER and, if unanswered, triggers the WhatsApp
        # fallback directly — never fabricated here (CLAUDE.md §25).
        await db.commit()
        log_with_fields(
            logger, logging.INFO, "n8n_attempt_call", lead_id=str(lead.id), outcome="initiated"
        )
        return CallAttemptResult(attempted=True, outcome="initiated", lead_status="CONTACTING")

    new_status = "CONTACTED" if handle.status == "answered" else "NO_ANSWER"
    await leads_service.transition_lead_status(db, lead, new_status)
    await db.commit()

    log_with_fields(
        logger, logging.INFO, "n8n_attempt_call", lead_id=str(lead.id), outcome=handle.status
    )
    return CallAttemptResult(attempted=True, outcome=handle.status, lead_status=new_status)


# Workflow B — n8n calls this after Wait + re-checking status, only when
# the lead is still NO_ANSWER (i.e. hasn't booked/been reached some other
# way in the meantime).
@router.post("/leads/{lead_id}/whatsapp-followup", response_model=WhatsAppFollowupResult)
async def whatsapp_followup(
    lead_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WhatsAppFollowupResult:
    lead = await _get_lead_or_404(db, clinic_id, lead_id)

    if lead.status != "NO_ANSWER":
        return WhatsAppFollowupResult(
            sent=False, lead_status=lead.status, reason="lead is not awaiting a WhatsApp followup"
        )

    to = lead.whatsapp or lead.phone
    if not to:
        raise _validation_error("Lead has no WhatsApp/phone number to message.")

    treatment_name = None
    if lead.treatment_id:
        treatment = await catalog_repo.get_treatment(db, clinic_id, lead.treatment_id)
        treatment_name = treatment.name if treatment else None

    text = (
        f"Hi {lead.name}, sorry we missed you on the phone! "
        + (f"We'd love to help with your {treatment_name} enquiry — " if treatment_name else "")
        + "reply here anytime and we'll take it from here."
    )
    provider = get_whatsapp_provider()
    handle = await provider.send_message(to=to, text=text)

    conversation = await conversations_repo.get_latest_conversation_by_channel(
        db, clinic_id, lead.id, "whatsapp"
    )
    if conversation is None:
        conversation = await conversations_repo.create_conversation(
            db, clinic_id, lead.id, "whatsapp"
        )
    await conversations_repo.create_message(
        db, conversation.id, direction="outbound", sender_type="ai", content=text
    )
    await leads_service.transition_lead_status(db, lead, "WHATSAPP_FOLLOWUP")
    await db.commit()

    log_with_fields(logger, logging.INFO, "n8n_whatsapp_followup", lead_id=str(lead.id))
    return WhatsAppFollowupResult(
        sent=handle.sent, lead_status="WHATSAPP_FOLLOWUP", conversation_id=conversation.id
    )


# Workflow E — n8n's own Schedule Trigger polls this periodically rather
# than FastAPI tracking reminder timing itself (CLAUDE.md §6).
@router.get("/appointments/reminders-due", response_model=ReminderCandidatesRead)
async def reminders_due(
    clinic_id: Annotated[uuid.UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    within_minutes: Annotated[int, Query(ge=1, le=10080)] = 1440,
) -> ReminderCandidatesRead:
    now = datetime.now(UTC)
    appointments = await appointments_repo.list_appointments_needing_reminder(
        db, clinic_id, now, now + timedelta(minutes=within_minutes)
    )
    return ReminderCandidatesRead(
        appointments=[
            ReminderCandidate(
                appointment_id=a.id, lead_id=a.lead_id, start=a.start, location=a.location
            )
            for a in appointments
            if a.start is not None
        ]
    )


@router.post("/appointments/{appointment_id}/reminder-sent", response_model=WebhookActionResult)
async def send_reminder(
    appointment_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WebhookActionResult:
    appointment = await _get_appointment_or_404(db, clinic_id, appointment_id)
    if await appointments_repo.has_appointment_event(db, appointment.id, "reminder_sent"):
        return WebhookActionResult(done=False, reason="reminder already sent")

    lead = await _get_lead_or_404(db, clinic_id, appointment.lead_id)
    clinic = await clinics_repo.get_clinic(db, clinic_id)
    if clinic is None:
        raise _not_found("Clinic")
    to = lead.whatsapp or lead.phone
    if not to:
        raise _validation_error("Lead has no WhatsApp/phone number to message.")

    when = (
        appointment.start.strftime("%A %d %B at %H:%M")
        if appointment.start
        else "your upcoming visit"
    )
    text = (
        f"Reminder: your appointment at {clinic.name} is {when}. "
        "Reply here if you need to reschedule."
    )
    provider = get_whatsapp_provider()
    handle = await provider.send_message(to=to, text=text)

    await appointments_repo.add_appointment_event(
        db, appointment.id, "reminder_sent", metadata={"channel": "whatsapp"}
    )
    await events_repo.create_event(
        db,
        clinic_id=clinic_id,
        event_type="appointment_reminder_sent",
        source="n8n",
        lead_id=lead.id,
        appointment_id=appointment.id,
    )
    await db.commit()
    return WebhookActionResult(done=handle.sent)


# Workflow C (Phase 8 naming — CLAUDE.md §17 Workflow D) — n8n calls these
# two after receiving appointment.status_changed(to_status="booked").
@router.post("/appointments/{appointment_id}/notify-clinic", response_model=WebhookActionResult)
async def notify_clinic_of_booking(
    appointment_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WebhookActionResult:
    appointment = await _get_appointment_or_404(db, clinic_id, appointment_id)
    if await appointments_repo.has_appointment_event(db, appointment.id, "clinic_notified"):
        return WebhookActionResult(done=False, reason="clinic already notified")

    lead = await _get_lead_or_404(db, clinic_id, appointment.lead_id)
    clinic = await clinics_repo.get_clinic(db, clinic_id)
    if clinic is None:
        raise _not_found("Clinic")
    if not clinic.email:
        await appointments_repo.add_appointment_event(
            db, appointment.id, "clinic_notified", metadata={"skipped": "no clinic email on file"}
        )
        await db.commit()
        return WebhookActionResult(done=False, reason="clinic has no notification email configured")

    when = appointment.start.isoformat() if appointment.start else "time to be confirmed"
    provider = get_email_provider()
    handle = await provider.send(
        to=clinic.email,
        subject=f"Appointment booked: {lead.name}",
        body=f"{lead.name} is booked for {when}.\nPhone: {lead.phone or 'not provided'}",
        clinic_id=clinic_id,
    )
    await appointments_repo.add_appointment_event(
        db, appointment.id, "clinic_notified", metadata={"provider": handle.provider}
    )
    await db.commit()
    return WebhookActionResult(done=handle.sent)


@router.post("/appointments/{appointment_id}/confirmation", response_model=WebhookActionResult)
async def send_confirmation(
    appointment_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WebhookActionResult:
    appointment = await _get_appointment_or_404(db, clinic_id, appointment_id)
    if await appointments_repo.has_appointment_event(db, appointment.id, "confirmation_sent"):
        return WebhookActionResult(done=False, reason="confirmation already sent")

    lead = await _get_lead_or_404(db, clinic_id, appointment.lead_id)
    clinic = await clinics_repo.get_clinic(db, clinic_id)
    if clinic is None:
        raise _not_found("Clinic")
    to = lead.whatsapp or lead.phone
    if not to:
        raise _validation_error("Lead has no WhatsApp/phone number to message.")

    when = (
        appointment.start.strftime("%A %d %B at %H:%M")
        if appointment.start
        else "the time we discussed"
    )
    text = f"You're confirmed at {clinic.name} for {when}. We look forward to seeing you!"
    provider = get_whatsapp_provider()
    handle = await provider.send_message(to=to, text=text)

    await appointments_repo.add_appointment_event(
        db, appointment.id, "confirmation_sent", metadata={"channel": "whatsapp"}
    )
    await db.commit()
    return WebhookActionResult(done=handle.sent)


# Workflow E (Phase 8 naming — CLAUDE.md §17 Workflow F) — n8n calls this
# after receiving appointment.status_changed(to_status="no_show"). Staff
# marking an appointment no-show (existing PATCH /appointments/{id}/status
# route) is the real, human-verified signal this reacts to — nothing here
# tries to auto-detect a no-show itself (CLAUDE.md §25 never fabricate).
@router.post("/appointments/{appointment_id}/no-show-followup", response_model=WebhookActionResult)
async def no_show_followup(
    appointment_id: uuid.UUID,
    clinic_id: Annotated[uuid.UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WebhookActionResult:
    appointment = await _get_appointment_or_404(db, clinic_id, appointment_id)
    if appointment.status != "no_show":
        raise _validation_error("Appointment is not marked no_show.")
    if await appointments_repo.has_appointment_event(db, appointment.id, "no_show_followup_sent"):
        return WebhookActionResult(done=False, reason="no-show followup already sent")

    lead = await _get_lead_or_404(db, clinic_id, appointment.lead_id)
    clinic = await clinics_repo.get_clinic(db, clinic_id)
    if clinic is None:
        raise _not_found("Clinic")
    to = lead.whatsapp or lead.phone
    if not to:
        raise _validation_error("Lead has no WhatsApp/phone number to message.")

    text = (
        f"Hi {lead.name}, we missed you at {clinic.name} today — no worries! "
        "Reply here whenever you'd like to find a new time."
    )
    provider = get_whatsapp_provider()
    handle = await provider.send_message(to=to, text=text)

    await appointments_repo.add_appointment_event(
        db, appointment.id, "no_show_followup_sent", metadata={"channel": "whatsapp"}
    )
    await leads_service.transition_lead_status(db, lead, "REACTIVATION")
    await db.commit()
    return WebhookActionResult(done=handle.sent)
