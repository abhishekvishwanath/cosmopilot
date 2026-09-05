import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.visitor_session import VisitorSession


async def create_visitor_session(
    db: AsyncSession,
    clinic_id: uuid.UUID,
    treatment_id: uuid.UUID | None = None,
    source: str | None = None,
    campaign: str | None = None,
    landing_page: str | None = None,
    anonymous_id: str | None = None,
) -> VisitorSession:
    visitor_session = VisitorSession(
        clinic_id=clinic_id,
        treatment_id=treatment_id,
        source=source,
        campaign=campaign,
        landing_page=landing_page,
        anonymous_id=anonymous_id,
    )
    db.add(visitor_session)
    await db.flush()
    return visitor_session
