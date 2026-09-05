import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

APPOINTMENT_STATUSES = ("pending", "booked", "confirmed", "cancelled", "completed", "no_show")


class AppointmentBase(BaseModel):
    lead_id: uuid.UUID
    doctor_id: uuid.UUID | None = None
    treatment_id: uuid.UUID | None = None
    start: datetime | None = None
    end: datetime | None = None
    location: str | None = None


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    doctor_id: uuid.UUID | None = None
    treatment_id: uuid.UUID | None = None
    start: datetime | None = None
    end: datetime | None = None
    location: str | None = None


class AppointmentStatusUpdate(BaseModel):
    status: str
    reason: str | None = None


class AppointmentRead(AppointmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    external_id: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class AppointmentEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    appointment_id: uuid.UUID
    event_type: str
    event_metadata: dict | None
    timestamp: datetime
