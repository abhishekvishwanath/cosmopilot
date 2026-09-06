from functools import lru_cache

from app.providers.calendar.base import (
    CalendarBooking,
    CalendarError,
    CalendarProvider,
    CalendarSlot,
)
from app.providers.calendar.mock import MockCalendarProvider

__all__ = [
    "CalendarBooking",
    "CalendarError",
    "CalendarProvider",
    "CalendarSlot",
    "get_calendar_provider",
]


@lru_cache
def get_calendar_provider() -> CalendarProvider:
    # No real PMS/calendar adapter yet — CLAUDE.md §32 says never invent an
    # integration before a clinic's actual scheduling platform is
    # identified. Swap this for a real adapter (reading provider config
    # from Settings) once one is; no caller of get_calendar_provider()
    # needs to change. @lru_cache makes this a singleton for the life of
    # the process, which is what lets MockCalendarProvider's in-memory
    # booked-slot state stay consistent across requests.
    return MockCalendarProvider()
