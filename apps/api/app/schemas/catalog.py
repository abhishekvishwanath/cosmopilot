import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DoctorBase(BaseModel):
    name: str
    title: str | None = None
    specialties: list[str] | None = None
    credentials: str | None = None
    bio: str | None = None
    photo_url: str | None = None


class DoctorCreate(DoctorBase):
    pass


class DoctorUpdate(BaseModel):
    name: str | None = None
    title: str | None = None
    specialties: list[str] | None = None
    credentials: str | None = None
    bio: str | None = None
    photo_url: str | None = None
    status: str | None = None


class DoctorRead(DoctorBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime


class TreatmentBase(BaseModel):
    name: str
    category: str | None = None
    description: str | None = None
    approved_information: str | None = None
    faq: list[dict] | None = None
    price_guidance: str | None = None
    duration: str | None = None
    booking_enabled: bool = True


class TreatmentCreate(TreatmentBase):
    pass


class TreatmentUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    approved_information: str | None = None
    faq: list[dict] | None = None
    price_guidance: str | None = None
    duration: str | None = None
    booking_enabled: bool | None = None
    status: str | None = None


class TreatmentRead(TreatmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
