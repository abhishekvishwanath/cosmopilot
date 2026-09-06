import itertools
import logging
import uuid

from app.core.logging import log_with_fields
from app.providers.voice.base import CallHandle, CallStatus, VoiceProvider

logger = logging.getLogger("cosmopilot.providers.voice")


class MockVoiceProvider(VoiceProvider):
    """
    Simulates a call outcome instead of placing a real one (CLAUDE.md §26)
    — deterministically alternating answered/no-answer per the demo
    scenarios in CLAUDE.md §36 (a successful call, and a missed call that
    falls back to WhatsApp), rather than random, so the demo is
    reproducible. State lives in-process (this class is a
    `get_voice_provider()` singleton) — fine for a single-process
    prototype demo, same as MockCalendarProvider.
    """

    def __init__(self) -> None:
        self._counter = itertools.count()

    async def start_call(
        self,
        *,
        to: str,
        clinic_name: str,
        lead_name: str,
        clinic_id: uuid.UUID | None = None,
        lead_id: uuid.UUID | None = None,
        treatment_name: str | None = None,
    ) -> CallHandle:
        call_id = uuid.uuid4().hex
        answered = next(self._counter) % 2 == 0
        status: CallStatus = "answered" if answered else "no_answer"
        log_with_fields(
            logger,
            logging.INFO,
            "mock_call_attempt",
            to=to,
            clinic_name=clinic_name,
            call_id=call_id,
            status=status,
        )
        return CallHandle(call_id=call_id, status=status)
