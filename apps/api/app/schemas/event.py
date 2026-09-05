import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    lead_id: uuid.UUID | None
    appointment_id: uuid.UUID | None
    source: str | None
    event_type: str
    event_metadata: dict | None
    timestamp: datetime
