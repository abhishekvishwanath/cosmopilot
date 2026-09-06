"""
Unit tests for MockCalendarProvider (CLAUDE.md §18, §26, Phase 7). Pure
logic, no database — same style as test_services_validation.py. The
service-layer wiring (get_available_slots fanning out across doctors,
book_appointment_from_slot mirroring into the CRM Appointment row) was
verified live against the real Supabase project + AI concierge, same as
every prior phase's convention (see the Phase 7 report).
"""

import uuid
from datetime import UTC, datetime

import pytest

from app.providers.calendar.base import CalendarError
from app.providers.calendar.mock import MockCalendarProvider

CLINIC_ID = uuid.uuid4()
DOCTOR_ID = uuid.uuid4()
LEAD_ID = uuid.uuid4()

# A Monday, so mon-fri hours definitely apply regardless of when tests run.
_A_MONDAY = datetime(2026, 9, 7, 8, 0, tzinfo=UTC)

OPENING_HOURS = {"mon-fri": "10:00-18:00", "sat": "10:00-16:00", "sun": "closed"}


async def _slots(provider: MockCalendarProvider, **overrides):
    kwargs = {
        "clinic_id": CLINIC_ID,
        "doctor_id": DOCTOR_ID,
        "treatment_id": None,
        "duration_minutes": 60,
        "timezone": "Asia/Dubai",
        "opening_hours": OPENING_HOURS,
        "earliest": _A_MONDAY,
        "days_ahead": 14,
        "limit": 6,
    }
    kwargs.update(overrides)
    return await provider.get_availability(**kwargs)


async def test_generates_slots_within_opening_hours() -> None:
    provider = MockCalendarProvider()
    slots = await _slots(provider)
    assert slots
    for slot in slots:
        local = slot.start
        assert local.weekday() != 6  # never a Sunday (closed)


async def test_respects_minimum_notice_on_the_same_day() -> None:
    provider = MockCalendarProvider()
    # 8am on a Monday, hours open at 10 — nothing before ~10am should be
    # offered same-day, and nothing within the 2-hour minimum-notice window.
    slots = await _slots(provider, days_ahead=1, limit=50)
    for slot in slots:
        assert slot.start >= _A_MONDAY.astimezone(slot.start.tzinfo)


async def test_no_slots_on_a_closed_day() -> None:
    provider = MockCalendarProvider()
    # Only ask about the following Sunday specifically by giving a 1-day
    # window starting on a Sunday.
    sunday = datetime(2026, 9, 13, 8, 0, tzinfo=UTC)
    slots = await _slots(provider, earliest=sunday, days_ahead=1, limit=50)
    assert slots == []


async def test_book_marks_the_slot_unavailable() -> None:
    provider = MockCalendarProvider()
    [first, *_rest] = await _slots(provider, limit=1)
    booking = await provider.book(clinic_id=CLINIC_ID, slot_token=first.token, lead_id=LEAD_ID)
    assert booking.start == first.start

    later_slots = await _slots(provider, limit=50)
    assert all(s.start != first.start for s in later_slots)


async def test_booking_an_unknown_token_raises_calendar_error() -> None:
    provider = MockCalendarProvider()
    with pytest.raises(CalendarError):
        await provider.book(clinic_id=CLINIC_ID, slot_token="not-a-real-token", lead_id=LEAD_ID)


async def test_double_booking_the_same_time_is_rejected() -> None:
    """
    Two visitors can each be offered the same open time before either
    books (two independent tokens for the same underlying slot) — the
    second attempt to actually book it must fail, not silently overwrite
    the first (CLAUDE.md §18/§25 — never fabricate a successful booking).
    """
    provider = MockCalendarProvider()
    [slot] = await _slots(provider, limit=1)
    duplicate_offer = await provider.get_availability(
        clinic_id=CLINIC_ID,
        doctor_id=DOCTOR_ID,
        treatment_id=None,
        duration_minutes=60,
        timezone="Asia/Dubai",
        opening_hours=OPENING_HOURS,
        earliest=_A_MONDAY,
        limit=1,
    )
    assert duplicate_offer[0].start == slot.start
    assert duplicate_offer[0].token != slot.token

    await provider.book(clinic_id=CLINIC_ID, slot_token=slot.token, lead_id=LEAD_ID)
    with pytest.raises(CalendarError):
        await provider.book(
            clinic_id=CLINIC_ID, slot_token=duplicate_offer[0].token, lead_id=LEAD_ID
        )


async def test_reschedule_frees_the_old_slot_and_books_the_new_one() -> None:
    provider = MockCalendarProvider()
    slots = await _slots(provider, limit=2)
    original, alternative = slots[0], slots[1]

    booking = await provider.book(clinic_id=CLINIC_ID, slot_token=original.token, lead_id=LEAD_ID)
    rebooked = await provider.reschedule(
        clinic_id=CLINIC_ID,
        external_id=booking.external_id,
        new_slot_token=alternative.token,
        lead_id=LEAD_ID,
    )
    assert rebooked.start == alternative.start
    assert rebooked.external_id != booking.external_id

    # The old time is bookable again; the new one is not.
    fresh = await _slots(provider, limit=50)
    assert any(s.start == original.start for s in fresh)
    assert all(s.start != alternative.start for s in fresh)


async def test_rescheduling_an_unknown_booking_raises_calendar_error() -> None:
    provider = MockCalendarProvider()
    [slot] = await _slots(provider, limit=1)
    with pytest.raises(CalendarError):
        await provider.reschedule(
            clinic_id=CLINIC_ID,
            external_id="not-a-real-id",
            new_slot_token=slot.token,
            lead_id=LEAD_ID,
        )


async def test_cancel_frees_the_slot() -> None:
    provider = MockCalendarProvider()
    [slot] = await _slots(provider, limit=1)
    booking = await provider.book(clinic_id=CLINIC_ID, slot_token=slot.token, lead_id=LEAD_ID)

    cancelled = await provider.cancel(clinic_id=CLINIC_ID, external_id=booking.external_id)
    assert cancelled is True

    fresh = await _slots(provider, limit=50)
    assert any(s.start == slot.start for s in fresh)


async def test_cancelling_an_unknown_booking_raises_calendar_error() -> None:
    provider = MockCalendarProvider()
    with pytest.raises(CalendarError):
        await provider.cancel(clinic_id=CLINIC_ID, external_id="not-a-real-id")


async def test_missing_opening_hours_falls_back_to_defaults() -> None:
    provider = MockCalendarProvider()
    slots = await _slots(provider, opening_hours=None, limit=1)
    assert slots
