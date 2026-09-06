import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.clinic import Clinic
from app.models.lead import Lead
from app.providers.calendar import CalendarSlot, get_calendar_provider
from app.repositories import appointments as appointments_repo
from app.repositories import catalog as catalog_repo
from app.repositories import clinics as clinics_repo
from app.repositories import events as events_repo
from app.schemas.appointment import APPOINTMENT_STATUSES
from app.services.leads import transition_lead_status
from app.services.n8n import notify_appointment_status_changed

# The prototype books a fixed-length slot regardless of treatment — none of
# CLAUDE.md's data model fields for Treatment are a structured duration
# (`duration` is free text like "2-3 hours" meant for display, not
# scheduling math). Revisit once a real PMS integration needs per-treatment
# durations.
DEFAULT_APPOINTMENT_DURATION_MINUTES = 60

# Booking/confirming/attending/cancelling an appointment moves the linked
# lead's status to match (CLAUDE.md §17 Workflow D, §9's lead states mirror
# appointment outcomes on purpose). Only moves the lead forward for
# "no_show" / "cancelled", which are terminal/recovery states regardless of
# where the lead was.
_APPOINTMENT_TO_LEAD_STATUS = {
    "booked": "BOOKED",
    "confirmed": "CONFIRMED",
    "completed": "ATTENDED",
    "cancelled": "CANCELLED",
    "no_show": "NO_SHOW",
}


def _validation_error(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"error": {"code": "validation_error", "message": message, "details": {}}},
    )


async def create_appointment(db: AsyncSession, clinic_id: uuid.UUID, data: dict) -> Appointment:
    appointment = Appointment(clinic_id=clinic_id, **data)
    db.add(appointment)
    await db.flush()

    await appointments_repo.add_appointment_event(db, appointment.id, "appointment_created")
    await events_repo.create_event(
        db,
        clinic_id=clinic_id,
        event_type="appointment_created",
        source="crm",
        lead_id=appointment.lead_id,
        appointment_id=appointment.id,
    )
    await db.flush()
    return appointment


async def transition_appointment_status(
    db: AsyncSession,
    appointment: Appointment,
    new_status: str,
    lead: Lead,
    reason: str | None = None,
) -> Appointment:
    """
    The only sanctioned way to change an appointment's status — never set
    directly by the AI concierge without going through backend validation
    (CLAUDE.md §15: "never independently mark an appointment as booked").
    Cascades the linked lead's status and writes both audit trails
    (appointment_events for the appointment, events for the funnel).
    """
    if new_status not in APPOINTMENT_STATUSES:
        raise _validation_error(
            f"'{new_status}' is not a valid appointment status. "
            f"Allowed: {', '.join(APPOINTMENT_STATUSES)}."
        )

    previous_status = appointment.status
    appointment.status = new_status
    await db.flush()

    await appointments_repo.add_appointment_event(
        db,
        appointment.id,
        "status_changed",
        metadata={"from": previous_status, "to": new_status, "reason": reason},
    )
    await events_repo.create_event(
        db,
        clinic_id=appointment.clinic_id,
        event_type="appointment_status_changed",
        source="crm",
        lead_id=appointment.lead_id,
        appointment_id=appointment.id,
        metadata={"from": previous_status, "to": new_status},
    )

    mapped_lead_status = _APPOINTMENT_TO_LEAD_STATUS.get(new_status)
    if mapped_lead_status and lead.status != mapped_lead_status:
        await transition_lead_status(db, lead, mapped_lead_status)

    await db.flush()

    # Fire-and-forget: n8n reacts to whichever transitions its workflows
    # care about (booked -> notify clinic + confirm; no_show -> recovery
    # message). This is the single choke point for every appointment
    # status change (CLAUDE.md's own docstring above), so it's the right
    # place to notify regardless of which caller changed the status.
    await notify_appointment_status_changed(
        appointment_id=appointment.id,
        lead_id=appointment.lead_id,
        clinic_id=appointment.clinic_id,
        from_status=previous_status,
        to_status=new_status,
    )
    return appointment


async def _opening_hours(db: AsyncSession, clinic_id: uuid.UUID) -> dict[str, str] | None:
    locations = await clinics_repo.list_locations(db, clinic_id)
    return locations[0].opening_hours if locations else None


async def get_available_slots(
    db: AsyncSession,
    clinic: Clinic,
    *,
    doctor_id: uuid.UUID | None = None,
    treatment_id: uuid.UUID | None = None,
    limit: int = 6,
) -> list[CalendarSlot]:
    """
    Fans out across the clinic's active doctors when no specific doctor is
    requested — MockCalendarProvider has no DB access of its own (same as
    every other provider), so "which doctors exist" is resolved here and
    passed down, keeping the provider a pure function of its inputs.
    """
    provider = get_calendar_provider()
    opening_hours = await _opening_hours(db, clinic.id)

    if doctor_id is not None:
        candidate_doctor_ids: list[uuid.UUID | None] = [doctor_id]
    else:
        doctors = await catalog_repo.list_active_doctors(db, clinic.id)
        candidate_doctor_ids = [d.id for d in doctors] or [None]

    slots: list[CalendarSlot] = []
    for candidate_id in candidate_doctor_ids:
        slots.extend(
            await provider.get_availability(
                clinic_id=clinic.id,
                doctor_id=candidate_id,
                treatment_id=treatment_id,
                duration_minutes=DEFAULT_APPOINTMENT_DURATION_MINUTES,
                timezone=clinic.timezone,
                opening_hours=opening_hours,
                earliest=datetime.now(UTC),
                limit=limit,
            )
        )
    slots.sort(key=lambda s: s.start)
    return slots[:limit]


async def book_appointment_from_slot(
    db: AsyncSession,
    clinic: Clinic,
    lead: Lead,
    *,
    slot_token: str,
    treatment_id: uuid.UUID | None = None,
) -> Appointment:
    """
    Books through the CalendarProvider first — the provider is the source
    of truth (CLAUDE.md §18) — then mirrors the confirmed booking into the
    CRM's own Appointment record. Never marks an appointment "booked"
    without that provider confirmation (CLAUDE.md §15/§25).
    """
    provider = get_calendar_provider()
    booking = await provider.book(clinic_id=clinic.id, slot_token=slot_token, lead_id=lead.id)

    appointment = await create_appointment(
        db,
        clinic.id,
        {
            "lead_id": lead.id,
            "doctor_id": booking.doctor_id,
            "treatment_id": treatment_id,
            "external_id": booking.external_id,
            "start": booking.start,
            "end": booking.end,
            "location": booking.location,
        },
    )
    return await transition_appointment_status(db, appointment, "booked", lead)


async def reschedule_appointment_to_slot(
    db: AsyncSession,
    clinic: Clinic,
    lead: Lead,
    appointment: Appointment,
    *,
    slot_token: str,
) -> Appointment:
    provider = get_calendar_provider()
    booking = await provider.reschedule(
        clinic_id=clinic.id,
        external_id=appointment.external_id or "",
        new_slot_token=slot_token,
        lead_id=lead.id,
    )
    updated = await appointments_repo.update_appointment(
        db,
        appointment,
        {
            "doctor_id": booking.doctor_id,
            "external_id": booking.external_id,
            "start": booking.start,
            "end": booking.end,
            "location": booking.location,
        },
    )
    await appointments_repo.add_appointment_event(
        db, appointment.id, "rescheduled", metadata={"new_start": booking.start.isoformat()}
    )
    await events_repo.create_event(
        db,
        clinic_id=clinic.id,
        event_type="appointment_rescheduled",
        source="crm",
        lead_id=lead.id,
        appointment_id=appointment.id,
    )
    await db.flush()
    return updated


async def cancel_appointment_with_provider(
    db: AsyncSession, clinic: Clinic, lead: Lead, appointment: Appointment
) -> Appointment:
    if appointment.external_id:
        provider = get_calendar_provider()
        await provider.cancel(clinic_id=clinic.id, external_id=appointment.external_id)
    return await transition_appointment_status(db, appointment, "cancelled", lead)
