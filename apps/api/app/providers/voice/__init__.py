from functools import lru_cache

from app.providers.voice.base import CallHandle, VoiceProvider
from app.providers.voice.mock import MockVoiceProvider

__all__ = ["CallHandle", "VoiceProvider", "get_voice_provider"]


@lru_cache
def get_voice_provider() -> VoiceProvider:
    # No Vapi adapter yet — CLAUDE.md §32 says request credentials only
    # when the phase that needs them starts (Phase 10). Swap this for a
    # VapiVoiceProvider (reading VAPI_API_KEY from Settings) once real
    # calling is required — no caller of get_voice_provider() needs to
    # change. @lru_cache makes this a singleton so MockVoiceProvider's
    # alternating counter stays consistent across requests.
    return MockVoiceProvider()
