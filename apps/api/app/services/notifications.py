from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinic import Clinic
from app.models.lead import Lead
from app.providers.email import get_email_provider
from app.repositories import events as events_repo


async def notify_clinic_of_new_lead(
    db: AsyncSession, clinic: Clinic, lead: Lead, treatment_name: str | None
) -> None:
    """
    CLAUDE.md §13 "clinic notification" step. Fails safely: an email
    provider error never blocks lead creation — it's logged as a
    `clinic_notification_failed` event so staff can still see the lead in
    the CRM and a HUMAN_REQUIRED-style gap is visible in the timeline,
    rather than raising and losing the lead that was just captured.
    """
    subject = f"New enquiry: {lead.name}" + (f" — {treatment_name}" if treatment_name else "")
    body = (
        f"{lead.name} enquired"
        + (f" about {treatment_name}" if treatment_name else "")
        + f".\nPhone: {lead.phone or 'not provided'}"
        + f"\nEmail: {lead.email or 'not provided'}"
        + f"\nPreferred time: {lead.preferred_time or 'not specified'}"
        + f"\nSource: {lead.source or 'unknown'}"
    )

    provider = get_email_provider()
    to = clinic.email
    if to is None:
        await events_repo.create_event(
            db,
            clinic_id=clinic.id,
            event_type="clinic_notification_failed",
            source="system",
            lead_id=lead.id,
            metadata={"reason": "clinic has no notification email configured"},
        )
        return

    handle = await provider.send(to=to, subject=subject, body=body, clinic_id=clinic.id)
    await events_repo.create_event(
        db,
        clinic_id=clinic.id,
        event_type="clinic_notified" if handle.sent else "clinic_notification_failed",
        source="system",
        lead_id=lead.id,
        metadata={"channel": "email", "provider": handle.provider, "detail": handle.detail},
    )
