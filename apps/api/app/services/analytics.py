"""
Phase 11 funnel analytics (CLAUDE.md §22). Composes the aggregate queries
in app/repositories/analytics.py into the rates CLAUDE.md names — every
number here is computed from real rows, never estimated or guessed.

Two of CLAUDE.md §22's listed metrics are deliberately not implemented,
each for the same reason (never fabricate — CLAUDE.md §25):
- "Visitors" / visitor-to-lead conversion: no page-view tracking exists
  yet — visitor_sessions rows are only created at lead-submission time
  (see that model's own docstring), so they carry the same count as leads
  and would produce a meaningless always-100% rate.
- "Estimated attributed revenue": treatments.price_guidance is free text
  (CLAUDE.md §8's schema — no structured numeric price field), so any
  currency figure here would be parsed/guessed from prose, not a real
  number.
Both are called out explicitly in the response's `note` field rather than
silently omitted.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import analytics as analytics_repo
from app.repositories import leads as leads_repo
from app.schemas.analytics import (
    FunnelAnalytics,
    FunnelCounts,
    FunnelRates,
    SourceBreakdownRow,
    TreatmentBreakdownRow,
)

_NOTE = (
    "Visitor-to-lead conversion and estimated attributed revenue are not included: "
    "this prototype doesn't yet track pre-lead page views, and treatment pricing is "
    "free-text guidance rather than a structured number (see CLAUDE.md §8) — both "
    "would have to be guessed rather than computed. Every other figure here comes "
    "directly from stored leads/appointments/event rows."
)


def _safe_rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


async def get_funnel_analytics(db: AsyncSession, clinic_id: uuid.UUID) -> FunnelAnalytics:
    leads_by_status = await leads_repo.count_by_status(db, clinic_id)
    total_leads = sum(leads_by_status.values())

    ai_call_attempts = await analytics_repo.count_events(db, clinic_id, "ai_call_attempted")
    calls_answered = await analytics_repo.count_events(
        db, clinic_id, "ai_call_ended", outcome="CONTACTED"
    )
    calls_no_answer = await analytics_repo.count_events(
        db, clinic_id, "ai_call_ended", outcome="NO_ANSWER"
    )
    whatsapp_followups_sent = await analytics_repo.count_leads_ever_reached_status(
        db, clinic_id, "WHATSAPP_FOLLOWUP"
    )
    whatsapp_recovered = await analytics_repo.count_leads_recovered_via_whatsapp(db, clinic_id)
    qualified_leads = await analytics_repo.count_leads_ever_reached_status(
        db, clinic_id, "QUALIFIED"
    )
    appointment_intents = await analytics_repo.count_leads_ever_reached_status(
        db, clinic_id, "APPOINTMENT_INTENT"
    )
    appointments_booked = await analytics_repo.count_leads_ever_reached_status(
        db, clinic_id, "BOOKED"
    )
    appointments_confirmed = await analytics_repo.count_appointments_by_terminal_status(
        db, clinic_id, "confirmed"
    )
    attended = await analytics_repo.count_appointments_by_terminal_status(
        db, clinic_id, "completed"
    )
    no_show = await analytics_repo.count_appointments_by_terminal_status(db, clinic_id, "no_show")
    cancelled = await analytics_repo.count_appointments_by_terminal_status(
        db, clinic_id, "cancelled"
    )

    by_source = await analytics_repo.count_leads_by_source(db, clinic_id)
    booked_by_source = await analytics_repo.count_booked_appointments_by_source(db, clinic_id)
    by_treatment = await analytics_repo.count_booked_appointments_by_treatment(db, clinic_id)

    calls_resolved = calls_answered + calls_no_answer
    attended_or_no_show = attended + no_show

    return FunnelAnalytics(
        counts=FunnelCounts(
            leads=total_leads,
            ai_call_attempts=ai_call_attempts,
            calls_answered=calls_answered,
            calls_no_answer=calls_no_answer,
            whatsapp_followups_sent=whatsapp_followups_sent,
            whatsapp_recovered=whatsapp_recovered,
            qualified_leads=qualified_leads,
            appointment_intents=appointment_intents,
            appointments_booked=appointments_booked,
            appointments_confirmed=appointments_confirmed,
            attended=attended,
            no_show=no_show,
            cancelled=cancelled,
        ),
        rates=FunnelRates(
            call_answer_rate=_safe_rate(calls_answered, calls_resolved),
            whatsapp_recovery_rate=_safe_rate(whatsapp_recovered, whatsapp_followups_sent),
            qualified_rate=_safe_rate(qualified_leads, total_leads),
            booking_rate=_safe_rate(appointments_booked, total_leads),
            attendance_rate=_safe_rate(attended, attended_or_no_show),
            no_show_rate=_safe_rate(no_show, attended_or_no_show),
        ),
        by_source=[
            SourceBreakdownRow(
                source=source, leads=count, appointments_booked=booked_by_source.get(source, 0)
            )
            for source, count in sorted(by_source.items(), key=lambda kv: -kv[1])
        ],
        by_treatment=[
            TreatmentBreakdownRow(treatment=name, appointments_booked=count)
            for name, count in sorted(by_treatment.items(), key=lambda kv: -kv[1])
        ],
        note=_NOTE,
    )
