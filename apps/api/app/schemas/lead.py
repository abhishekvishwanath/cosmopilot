import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.lead import LEAD_STATUSES


class LeadBase(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    treatment_id: uuid.UUID | None = None
    source: str | None = None
    landing_page: str | None = None
    preferred_time: str | None = None
    consent: bool = False


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    treatment_id: uuid.UUID | None = None
    preferred_time: str | None = None
    intent_score: int | None = None
    assigned_to: uuid.UUID | None = None


class LeadStatusUpdate(BaseModel):
    status: str

    @classmethod
    def allowed_statuses(cls) -> tuple[str, ...]:
        return LEAD_STATUSES


class LeadRead(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    intent_score: int | None
    status: str
    assigned_to: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class LeadPage(BaseModel):
    items: list[LeadRead]
    next_cursor: str | None = None
