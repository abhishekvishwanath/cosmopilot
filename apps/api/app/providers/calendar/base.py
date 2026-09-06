"""
CalendarProvider (CLAUDE.md §18, §27, Phase 7): availability, booking,
rescheduling, and cancellation. This is the interface CLAUDE.md is most
explicit about — "the appointment provider is the source of truth for
availability/booking/status. The LLM is never the source of truth" — so
every method here returns a fully resolved, typed result; nothing about a
booking is ever inferred or fabricated by a caller.

`CalendarSlot.token` is an opaque, provider-issued reference. Callers
(services/, agents/tools.py) round-trip it back into book()/reschedule()
verbatim — never parse or reconstruct it — so a real provider (Google
Calendar, a clinic PMS) can use a completely different internal shape
without any caller changing (docs/PROVIDER_INTERFACES.md's design rules).
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CalendarSlot:
    token: str
    start: datetime
    end: datetime
    doctor_id: uuid.UUID | None
    location: str | None


@dataclass(frozen=True)
class CalendarBooking:
    external_id: str
    start: datetime
    end: datetime
    doctor_id: uuid.UUID | None
    location: str | None


class CalendarError(Exception):
    """
    A calendar operation couldn't be completed (slot taken, unknown/expired
    token, unknown booking). The caller decides the graceful fallback
    (CLAUDE.md §25) — the provider itself never fabricates a success.
    """


class CalendarProvider(ABC):
    @abstractmethod
    async def get_availability(
        self,
        *,
        clinic_id: uuid.UUID,
        doctor_id: uuid.UUID | None,
        treatment_id: uuid.UUID | None,
        duration_minutes: int,
        timezone: str,
        opening_hours: dict[str, str] | None,
        earliest: datetime,
        days_ahead: int = 14,
        limit: int = 6,
    ) -> list[CalendarSlot]: ...

    @abstractmethod
    async def book(
        self, *, clinic_id: uuid.UUID, slot_token: str, lead_id: uuid.UUID
    ) -> CalendarBooking: ...

    @abstractmethod
    async def reschedule(
        self,
        *,
        clinic_id: uuid.UUID,
        external_id: str,
        new_slot_token: str,
        lead_id: uuid.UUID,
    ) -> CalendarBooking: ...

    @abstractmethod
    async def cancel(self, *, clinic_id: uuid.UUID, external_id: str) -> bool: ...
