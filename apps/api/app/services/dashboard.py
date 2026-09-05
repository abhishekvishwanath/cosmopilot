import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import appointments as appointments_repo
from app.repositories import leads as leads_repo
from app.schemas.dashboard import DashboardStats


async def get_dashboard_stats(db: AsyncSession, clinic_id: uuid.UUID) -> DashboardStats:
    leads_by_status = await leads_repo.count_by_status(db, clinic_id)
    appointments_by_status = await appointments_repo.count_by_status(db, clinic_id)
    upcoming_appointments = await appointments_repo.count_upcoming(db, clinic_id)

    return DashboardStats(
        total_leads=sum(leads_by_status.values()),
        leads_by_status=leads_by_status,
        upcoming_appointments=upcoming_appointments,
        appointments_by_status=appointments_by_status,
    )
