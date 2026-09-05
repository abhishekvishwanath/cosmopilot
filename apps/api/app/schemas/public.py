import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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


class PublicLeadCreate(BaseModel):
    """
    Enquiry-form intake (CLAUDE.md §13). Deliberately narrower than
    LeadCreate (schemas/lead.py) — `consent` is required (not defaulted),
    and it accepts the attribution/contact-preference fields the public
    form collects that a CRM staff member wouldn't need to supply by hand.
    """

    name: str = Field(min_length=2, max_length=200)
    phone: str = Field(min_length=7, max_length=50)
    email: str | None = None
    treatment_id: uuid.UUID | None = None
    preferred_time: str | None = Field(default=None, max_length=200)
    contact_method: Literal["Call", "WhatsApp", "Email"] | None = None
    consent: bool
    source: str | None = Field(default=None, max_length=100)
    campaign: str | None = Field(default=None, max_length=200)
    landing_page: str | None = Field(default=None, max_length=500)
    anonymous_id: str | None = Field(default=None, max_length=100)


class PublicLeadRead(BaseModel):
    id: uuid.UUID
    status: str
