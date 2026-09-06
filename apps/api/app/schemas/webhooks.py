import uuid
from datetime import datetime

from pydantic import BaseModel


class LeadStatusRead(BaseModel):
    lead_id: uuid.UUID
    status: str
    name: str
    phone: str | None
    whatsapp: str | None
    has_active_appointment: bool


class CallAttemptResult(BaseModel):
    attempted: bool
    outcome: str | None = None
    lead_status: str
    reason: str | None = None


class WhatsAppFollowupResult(BaseModel):
    sent: bool
    lead_status: str
    reason: str | None = None
    conversation_id: uuid.UUID | None = None


class ReminderCandidate(BaseModel):
    appointment_id: uuid.UUID
    lead_id: uuid.UUID
    start: datetime
    location: str | None


class ReminderCandidatesRead(BaseModel):
    appointments: list[ReminderCandidate]


class WebhookActionResult(BaseModel):
    done: bool
    reason: str | None = None
