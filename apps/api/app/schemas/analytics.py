from pydantic import BaseModel


class FunnelCounts(BaseModel):
    leads: int
    ai_call_attempts: int
    calls_answered: int
    calls_no_answer: int
    whatsapp_followups_sent: int
    whatsapp_recovered: int
    qualified_leads: int
    appointment_intents: int
    appointments_booked: int
    appointments_confirmed: int
    attended: int
    no_show: int
    cancelled: int


class FunnelRates(BaseModel):
    """
    Every rate is `None` when its denominator is zero — a clinic with no
    leads yet has no rate to report, and reporting 0% would misleadingly
    look like a real (bad) result rather than "no data" (CLAUDE.md §25 —
    never present a fabricated-looking number in place of missing data).
    """

    call_answer_rate: float | None
    whatsapp_recovery_rate: float | None
    qualified_rate: float | None
    booking_rate: float | None
    attendance_rate: float | None
    no_show_rate: float | None


class SourceBreakdownRow(BaseModel):
    source: str
    leads: int
    appointments_booked: int


class TreatmentBreakdownRow(BaseModel):
    treatment: str
    appointments_booked: int


class FunnelAnalytics(BaseModel):
    counts: FunnelCounts
    rates: FunnelRates
    by_source: list[SourceBreakdownRow]
    by_treatment: list[TreatmentBreakdownRow]
    note: str
