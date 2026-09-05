import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.lead import Lead
from app.repositories import appointments as appointments_repo
from app.repositories import events as events_repo
from app.schemas.appointment import APPOINTMENT_STATUSES
from app.services.leads import transition_lead_status

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
    return appointment
