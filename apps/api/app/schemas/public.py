import uuid

from pydantic import BaseModel, ConfigDict


class PublicLocationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    address: str | None = None
    city: str | None = None
    country: str | None = None
    phone: str | None = None
    opening_hours: dict | None = None
    timezone: str | None = None


class PublicClinicRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    website: str | None = None
    primary_phone: str | None = None
    email: str | None = None
    timezone: str
    locations: list[PublicLocationRead]


class PublicDoctorRead(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    title: str | None = None
    specialties: list[str] | None = None
    credentials: str | None = None
    bio: str | None = None
    photo_url: str | None = None


class PublicTreatmentRead(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    category: str | None = None
    description: str | None = None
    approved_information: str | None = None
    faq: list[dict] | None = None
    price_guidance: str | None = None
    duration: str | None = None
    booking_enabled: bool
