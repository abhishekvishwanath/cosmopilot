"""
get_voice_provider() factory branching (Phase 10) — mirrors the pattern in
test_webhook_auth.py for clearing the cached Settings singleton per test.
"""

import pytest

from app.core.config import get_settings
from app.providers.voice import get_voice_provider
from app.providers.voice.mock import MockVoiceProvider


def _reset(monkeypatch: pytest.MonkeyPatch) -> None:
    get_voice_provider.cache_clear()
    get_settings.cache_clear()


def test_defaults_to_mock_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VOICE_PROVIDER", raising=False)
    _reset(monkeypatch)

    assert isinstance(get_voice_provider(), MockVoiceProvider)


def test_vapi_provider_requires_full_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VOICE_PROVIDER", "vapi")
    monkeypatch.delenv("VAPI_API_KEY", raising=False)
    _reset(monkeypatch)

    with pytest.raises(RuntimeError, match="VAPI_API_KEY"):
        get_voice_provider()


def test_vapi_provider_selected_when_fully_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VOICE_PROVIDER", "vapi")
    monkeypatch.setenv("VAPI_API_KEY", "key")
    monkeypatch.setenv("VAPI_ASSISTANT_ID", "assistant-1")
    monkeypatch.setenv("VAPI_PHONE_NUMBER_ID", "phone-1")
    _reset(monkeypatch)

    from app.providers.voice.vapi import VapiVoiceProvider

    assert isinstance(get_voice_provider(), VapiVoiceProvider)

    monkeypatch.delenv("VOICE_PROVIDER", raising=False)
    monkeypatch.delenv("VAPI_API_KEY", raising=False)
    monkeypatch.delenv("VAPI_ASSISTANT_ID", raising=False)
    monkeypatch.delenv("VAPI_PHONE_NUMBER_ID", raising=False)
    _reset(monkeypatch)
