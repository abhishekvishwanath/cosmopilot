"""
MockCalendarProvider (CLAUDE.md §18, §26, Phase 7). Generates a realistic
slot grid from the clinic's own opening hours and enforces the same
constraint a real calendar would — no double-booking — without any real
PMS/calendar integration. State lives in-process (this class is a
`get_calendar_provider()` singleton, same pattern as the other mock
providers) — fine for a single-process prototype demo; a real adapter
(Phase 32's "identify the clinic's actual scheduling platform") replaces
this entirely without any caller changing.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.providers.calendar.base import (
    CalendarBooking,
    CalendarError,
    CalendarProvider,
    CalendarSlot,
)

_DAY_ORDER = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")

# Used only when a clinic location has no opening_hours on file — keeps the
# demo usable even for incomplete seed data, never presented as the
# clinic's real hours anywhere else in the app.
_DEFAULT_OPENING_HOURS = {"mon-fri": "10:00-18:00", "sat": "10:00-16:00", "sun": "closed"}

_SLOT_STEP_MINUTES = 60
# A visitor chatting right now shouldn't be offered a slot minutes away —
# no real clinic would treat a chat booking as a walk-in.
_MIN_NOTICE = timedelta(hours=2)


def _expand_days(opening_hours: dict[str, str]) -> dict[str, str]:
    expanded: dict[str, str] = {}
    for raw_key, value in opening_hours.items():
        key = raw_key.strip().lower()
        if "-" in key:
            start_day, _, end_day = key.partition("-")
            if start_day in _DAY_ORDER and end_day in _DAY_ORDER:
                start_i, end_i = _DAY_ORDER.index(start_day), _DAY_ORDER.index(end_day)
                for i in range(start_i, end_i + 1):
                    expanded[_DAY_ORDER[i]] = value
                continue
        expanded[key] = value
    return expanded


def _parse_window(value: str) -> tuple[time, time] | None:
    if value.strip().lower() == "closed":
        return None
    open_s, _, close_s = value.partition("-")
    return (
        datetime.strptime(open_s.strip(), "%H:%M").time(),
        datetime.strptime(close_s.strip(), "%H:%M").time(),
    )


@dataclass(frozen=True)
class _OfferedSlot:
    clinic_id: uuid.UUID
    doctor_id: uuid.UUID | None
    start: datetime
    end: datetime


@dataclass(frozen=True)
class _Booking:
    clinic_id: uuid.UUID
    doctor_id: uuid.UUID | None
    start: datetime
    end: datetime
    lead_id: uuid.UUID


class MockCalendarProvider(CalendarProvider):
    def __init__(self) -> None:
        # slot_token -> the slot it was offered for, until booked or
        # regenerated. external_id -> the active booking. _busy is the
        # (clinic, doctor, start-iso) index that both consult to avoid
        # double-booking or re-offering an already-booked time.
        self._pending: dict[str, _OfferedSlot] = {}
        self._bookings: dict[str, _Booking] = {}
        self._busy: set[tuple[uuid.UUID, uuid.UUID | None, str]] = set()

    def _busy_key(
        self, clinic_id: uuid.UUID, doctor_id: uuid.UUID | None, start: datetime
    ) -> tuple[uuid.UUID, uuid.UUID | None, str]:
        return (clinic_id, doctor_id, start.isoformat())

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
    ) -> list[CalendarSlot]:
        tz = ZoneInfo(timezone) if timezone else UTC
        hours_by_day = _expand_days(opening_hours or _DEFAULT_OPENING_HOURS)
        local_earliest = earliest.astimezone(tz)
        cutoff = local_earliest + _MIN_NOTICE

        slots: list[CalendarSlot] = []
        for offset in range(days_ahead):
            current_date = (local_earliest + timedelta(days=offset)).date()
            window = hours_by_day.get(_DAY_ORDER[current_date.weekday()])
            parsed = _parse_window(window) if window else None
            if parsed is None:
                continue
            open_time, close_time = parsed
            cursor = datetime.combine(current_date, open_time, tzinfo=tz)
            day_close = datetime.combine(current_date, close_time, tzinfo=tz)

            while cursor + timedelta(minutes=duration_minutes) <= day_close:
                if (
                    cursor >= cutoff
                    and self._busy_key(clinic_id, doctor_id, cursor) not in self._busy
                ):
                    end = cursor + timedelta(minutes=duration_minutes)
                    token = uuid.uuid4().hex
                    self._pending[token] = _OfferedSlot(
                        clinic_id=clinic_id, doctor_id=doctor_id, start=cursor, end=end
                    )
                    slots.append(
                        CalendarSlot(
                            token=token, start=cursor, end=end, doctor_id=doctor_id, location=None
                        )
                    )
                    if len(slots) >= limit:
                        return slots
                cursor += timedelta(minutes=_SLOT_STEP_MINUTES)
        return slots

    async def book(
        self, *, clinic_id: uuid.UUID, slot_token: str, lead_id: uuid.UUID
    ) -> CalendarBooking:
        offered = self._pending.get(slot_token)
        if offered is None or offered.clinic_id != clinic_id:
            raise CalendarError(
                "That time slot isn't available anymore — please check availability again."
            )
        key = self._busy_key(offered.clinic_id, offered.doctor_id, offered.start)
        if key in self._busy:
            raise CalendarError("That time slot was just booked — please choose another.")

        self._busy.add(key)
        external_id = uuid.uuid4().hex
        self._bookings[external_id] = _Booking(
            clinic_id=offered.clinic_id,
            doctor_id=offered.doctor_id,
            start=offered.start,
            end=offered.end,
            lead_id=lead_id,
        )
        del self._pending[slot_token]
        return CalendarBooking(
            external_id=external_id,
            start=offered.start,
            end=offered.end,
            doctor_id=offered.doctor_id,
            location=None,
        )

    async def reschedule(
        self,
        *,
        clinic_id: uuid.UUID,
        external_id: str,
        new_slot_token: str,
        lead_id: uuid.UUID,
    ) -> CalendarBooking:
        existing = self._bookings.get(external_id)
        if existing is None or existing.clinic_id != clinic_id:
            raise CalendarError("Unknown booking to reschedule.")

        # Book the new slot before releasing the old one — a failed
        # rebooking (e.g. the new slot was taken in the meantime) must
        # never destroy an existing confirmed booking.
        new_booking = await self.book(
            clinic_id=clinic_id, slot_token=new_slot_token, lead_id=lead_id
        )
        old_key = self._busy_key(existing.clinic_id, existing.doctor_id, existing.start)
        self._busy.discard(old_key)
        del self._bookings[external_id]
        return new_booking

    async def cancel(self, *, clinic_id: uuid.UUID, external_id: str) -> bool:
        existing = self._bookings.get(external_id)
        if existing is None or existing.clinic_id != clinic_id:
            raise CalendarError("Unknown booking to cancel.")
        key = self._busy_key(existing.clinic_id, existing.doctor_id, existing.start)
        self._busy.discard(key)
        del self._bookings[external_id]
        return True
