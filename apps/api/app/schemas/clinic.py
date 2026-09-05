import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClinicBase(BaseModel):
    name: str
    description: str | None = None
    website: str | None = None
    primary_phone: str | None = None
    email: str | None = None
    timezone: str = "Asia/Dubai"


class ClinicUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    website: str | None = None
    primary_phone: str | None = None
    email: str | None = None
    timezone: str | None = None
    status: str | None = None
    settings: dict | None = None


class ClinicRead(ClinicBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    settings: dict
    created_at: datetime
    updated_at: datetime


class ClinicLocationBase(BaseModel):
    address: str | None = None
    city: str | None = None
    country: str | None = None
    phone: str | None = None
    opening_hours: dict | None = None
    timezone: str | None = None


class ClinicLocationCreate(ClinicLocationBase):
    pass


class ClinicLocationUpdate(ClinicLocationBase):
    pass


class ClinicLocationRead(ClinicLocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
