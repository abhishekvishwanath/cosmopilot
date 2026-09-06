from functools import lru_cache

from app.core.config import get_settings
from app.providers.voice.base import CallHandle, VoiceProvider
from app.providers.voice.mock import MockVoiceProvider

__all__ = ["CallHandle", "VoiceProvider", "get_voice_provider"]


@lru_cache
def get_voice_provider() -> VoiceProvider:
    settings = get_settings()
    if settings.voice_provider == "vapi":
        if not settings.vapi_api_key:
            raise RuntimeError("VOICE_PROVIDER=vapi requires VAPI_API_KEY to be set.")
        if not settings.vapi_assistant_id:
            raise RuntimeError("VOICE_PROVIDER=vapi requires VAPI_ASSISTANT_ID to be set.")
        if not settings.vapi_phone_number_id:
            raise RuntimeError("VOICE_PROVIDER=vapi requires VAPI_PHONE_NUMBER_ID to be set.")
        from app.providers.voice.vapi import VapiVoiceProvider

        return VapiVoiceProvider(
            api_key=settings.vapi_api_key,
            assistant_id=settings.vapi_assistant_id,
            phone_number_id=settings.vapi_phone_number_id,
        )
    # @lru_cache makes this a singleton so MockVoiceProvider's alternating
    # counter stays consistent across requests.
    return MockVoiceProvider()
