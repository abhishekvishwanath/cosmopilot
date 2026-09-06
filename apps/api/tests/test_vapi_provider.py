"""
Unit tests for VapiVoiceProvider, mocking httpx the same way
test_groq_provider.py does — no real network call. The one behavior that
matters for correctness here: a real call's outcome isn't known yet when
`start_call` returns, so it must always report "initiated", never guess
answered/no_answer (CLAUDE.md §25) — that's the opposite of
MockVoiceProvider's synchronous outcome, covered in
test_voice_whatsapp_providers.py.
"""

import uuid
from typing import Any

import pytest

from app.providers.voice.vapi import VapiError, VapiVoiceProvider


class _FakeResponse:
    def __init__(self, status_code: int, body: dict[str, Any]):
        self.status_code = status_code
        self._body = body
        self.text = str(body)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx

            raise httpx.HTTPStatusError("error", request=None, response=self)  # type: ignore[arg-type]

    def json(self) -> dict[str, Any]:
        return self._body


class _FakeAsyncClient:
    def __init__(self, response: _FakeResponse):
        self._response = response
        self.last_json: dict[str, Any] | None = None
        self.last_headers: dict[str, str] | None = None

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        return None

    async def post(
        self, url: str, headers: dict[str, str], json: dict[str, Any]
    ) -> _FakeResponse:
        self.last_headers = headers
        self.last_json = json
        return self._response


async def test_start_call_reports_initiated_not_a_guessed_outcome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = _FakeAsyncClient(_FakeResponse(201, {"id": "call-abc123"}))
    monkeypatch.setattr("app.providers.voice.vapi.httpx.AsyncClient", lambda **_: fake_client)

    provider = VapiVoiceProvider(
        api_key="test-key", assistant_id="assistant-1", phone_number_id="phone-1"
    )
    lead_id = uuid.uuid4()
    clinic_id = uuid.uuid4()
    handle = await provider.start_call(
        to="+15551234567",
        clinic_name="Cosmo Dental Dubai",
        lead_name="Jane Doe",
        clinic_id=clinic_id,
        lead_id=lead_id,
        treatment_name="veneers",
    )

    assert handle.call_id == "call-abc123"
    assert handle.status == "initiated"


async def test_start_call_sends_lead_and_clinic_ids_as_metadata_for_webhook_correlation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = _FakeAsyncClient(_FakeResponse(201, {"id": "call-1"}))
    monkeypatch.setattr("app.providers.voice.vapi.httpx.AsyncClient", lambda **_: fake_client)

    provider = VapiVoiceProvider(api_key="k", assistant_id="a", phone_number_id="p")
    lead_id = uuid.uuid4()
    clinic_id = uuid.uuid4()
    await provider.start_call(
        to="+15551234567",
        clinic_name="Cosmo Dental Dubai",
        lead_name="Jane Doe",
        clinic_id=clinic_id,
        lead_id=lead_id,
    )

    sent = fake_client.last_json
    assert sent is not None
    metadata = sent["assistantOverrides"]["metadata"]
    assert metadata["lead_id"] == str(lead_id)
    assert metadata["clinic_id"] == str(clinic_id)
    assert sent["customer"]["number"] == "+15551234567"


async def test_start_call_raises_vapi_error_on_http_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = _FakeAsyncClient(_FakeResponse(401, {"message": "invalid key"}))
    monkeypatch.setattr("app.providers.voice.vapi.httpx.AsyncClient", lambda **_: fake_client)

    provider = VapiVoiceProvider(api_key="bad", assistant_id="a", phone_number_id="p")
    with pytest.raises(VapiError):
        await provider.start_call(to="+15551234567", clinic_name="Clinic", lead_name="Lead")
