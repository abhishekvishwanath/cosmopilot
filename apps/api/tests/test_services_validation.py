"""
Unit tests for the service-layer validation that guards lead/appointment
state transitions (CLAUDE.md §9, §15 — never derived from free-form text,
always backend-validated). These don't touch the database: an invalid
status is rejected before any DB read/write happens, so a bare object
stands in for the session/row without needing a real AsyncSession.

The full write path (successful transitions, event logging, the
appointment -> lead status cascade, RLS enforcement) was verified against
the real Supabase project during Phase 2 development — see the Phase 2
report. A DB-transaction-backed integration suite exercising that same
path automatically is a reasonable next investment, not yet built.
"""

from typing import Any, cast

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.lead import Lead
from app.services.appointments import transition_appointment_status
from app.services.leads import transition_lead_status


class _Unused:
    """Stands in for `db`/`lead`/`appointment` in tests where validation
    fails before either is touched — any attribute access is a bug."""

    def __getattr__(self, name: str) -> Any:
        raise AssertionError(f"unexpected access to `.{name}` — validation should fail first")


def _unused() -> Any:
    return _Unused()


async def test_lead_status_transition_rejects_unknown_status() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await transition_lead_status(
            cast(AsyncSession, _unused()), cast(Lead, _unused()), "NOT_A_REAL_STATUS"
        )
    assert exc_info.value.status_code == 422


async def test_appointment_status_transition_rejects_unknown_status() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await transition_appointment_status(
            cast(AsyncSession, _unused()),
            cast(Appointment, _unused()),
            "not_a_real_status",
            cast(Lead, _unused()),
        )
    assert exc_info.value.status_code == 422
