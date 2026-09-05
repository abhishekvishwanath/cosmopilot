import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import LEAD_STATUSES, Consent, Lead
from app.repositories import events as events_repo


def _validation_error(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"error": {"code": "validation_error", "message": message, "details": {}}},
    )


async def create_lead(db: AsyncSession, clinic_id: uuid.UUID, data: dict) -> Lead:
    """
    Creates a lead and records the funnel event that starts it — CLAUDE.md
    §22's Discovery -> Landing Page Visit -> Enquiry -> Lead funnel begins
    here. If consent was granted on submission, it's logged as an auditable
    Consent row, not just the summary boolean on the lead (CLAUDE.md §23).
    """
    consent_granted = data.get("consent", False)
    lead = Lead(clinic_id=clinic_id, **data)
    db.add(lead)
    await db.flush()

    if consent_granted:
        db.add(
            Consent(
                lead_id=lead.id,
                channel=data.get("source") or "unknown",
                consent_type="communication",
                granted=True,
                source="lead_creation",
            )
        )

    await events_repo.create_event(
        db,
        clinic_id=clinic_id,
        event_type="lead_created",
        source=data.get("source"),
        lead_id=lead.id,
    )
    await db.flush()
    return lead


async def transition_lead_status(
    db: AsyncSession, lead: Lead, new_status: str
) -> Lead:
    """
    The only sanctioned way to change a lead's status (CLAUDE.md §9 — never
    derived from free-form AI text). Every transition is logged to `events`
    so the CRM timeline (§19) always has a complete history.
    """
    if new_status not in LEAD_STATUSES:
        raise _validation_error(
            f"'{new_status}' is not a valid lead status. Allowed: {', '.join(LEAD_STATUSES)}."
        )

    previous_status = lead.status
    lead.status = new_status
    await db.flush()

    await events_repo.create_event(
        db,
        clinic_id=lead.clinic_id,
        event_type="lead_status_changed",
        source="crm",
        lead_id=lead.id,
        metadata={"from": previous_status, "to": new_status},
    )
    await db.flush()
    return lead
