from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ClinicPrincipal, get_current_clinic_staff
from app.db.session import get_db
from app.schemas.analytics import FunnelAnalytics
from app.schemas.dashboard import DashboardStats
from app.services import analytics as analytics_service
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardStats:
    return await dashboard_service.get_dashboard_stats(db, principal.clinic_id)


@router.get("/funnel", response_model=FunnelAnalytics)
async def get_funnel(
    principal: Annotated[ClinicPrincipal, Depends(get_current_clinic_staff)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FunnelAnalytics:
    return await analytics_service.get_funnel_analytics(db, principal.clinic_id)
