from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Basic CRM dashboard counts (CLAUDE.md §19). Full funnel analytics —
    answer rate, conversion rate, source/treatment breakdowns — are
    GET /analytics/funnel (app/schemas/analytics.py, Phase 11)."""

    total_leads: int
    leads_by_status: dict[str, int]
    upcoming_appointments: int
    appointments_by_status: dict[str, int]
