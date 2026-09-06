"""
Unit tests for the outbound n8n dispatcher (CLAUDE.md §25 — an
unreachable/unconfigured downstream integration must never block or fail
the request that triggered it). httpx mocked the same way
test_db_supabase.py and test_groq_provider.py do — no real network call.
"""

import uuid
from typing import Any

import pytest

from app.core.config import get_settings
from app.services.n8n import notify_appointment_status_changed, notify_lead_created, notify_n8n


class _FakeResponse:
    def __init__(self, status_code: int = 200):
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx

            raise httpx.HTTPStatusError("error", request=None, response=self)  # type: ignore[arg-type]


class _FakeAsyncClient:
    def __init__(self, response: _FakeResponse | None = None, raise_connect_error: bool = False):
        self._response = response or _FakeResponse()
        self._raise_connect_error = raise_connect_error
        self.last_url: str | None = None
        self.last_json: dict[str, Any] | None = None
        self.last_headers: dict[str, str] | None = None

    async def __aenter__(self) -> "_FakeAsyncClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        return None

    async def post(
        self, url: str, json: dict[str, Any], headers: dict[str, str]
    ) -> _FakeResponse:
        if self._raise_connect_error:
            import httpx

            raise httpx.ConnectError("connection refused")
        self.last_url = url
        self.last_json = json
        self.last_headers = headers
        return self._response


def _configure(monkeypatch: pytest.MonkeyPatch, **overrides: Any) -> None:
    for key, value in overrides.items():
        monkeypatch.setenv(key.upper(), value)
    get_settings.cache_clear()


async def test_notify_n8n_does_nothing_when_not_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("N8N_WEBHOOK_BASE_URL", raising=False)
    get_settings.cache_clear()

    fake_client = _FakeAsyncClient()
    monkeypatch.setattr("app.services.n8n.httpx.AsyncClient", lambda **_: fake_client)

    await notify_n8n("lead.created", {"lead_id": "abc"})

    assert fake_client.last_url is None


async def test_notify_n8n_posts_to_the_event_specific_url_with_secret_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(
        monkeypatch,
        n8n_webhook_base_url="https://example.app.n8n.cloud",
        n8n_webhook_shared_secret="shh",
    )
    fake_client = _FakeAsyncClient()
    monkeypatch.setattr("app.services.n8n.httpx.AsyncClient", lambda **_: fake_client)

    await notify_n8n("lead.created", {"lead_id": "abc"})

    assert fake_client.last_url == "https://example.app.n8n.cloud/webhook/lead.created"
    assert fake_client.last_json == {"lead_id": "abc"}
    assert fake_client.last_headers == {"X-Webhook-Secret": "shh"}


async def test_notify_n8n_never_raises_when_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure(monkeypatch, n8n_webhook_base_url="https://example.app.n8n.cloud")
    fake_client = _FakeAsyncClient(raise_connect_error=True)
    monkeypatch.setattr("app.services.n8n.httpx.AsyncClient", lambda **_: fake_client)

    await notify_n8n("lead.created", {"lead_id": "abc"})  # must not raise


async def test_notify_n8n_never_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _configure(monkeypatch, n8n_webhook_base_url="https://example.app.n8n.cloud")
    fake_client = _FakeAsyncClient(response=_FakeResponse(500))
    monkeypatch.setattr("app.services.n8n.httpx.AsyncClient", lambda **_: fake_client)

    await notify_n8n("lead.created", {"lead_id": "abc"})  # must not raise


async def test_notify_lead_created_dispatches_the_right_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(monkeypatch, n8n_webhook_base_url="https://example.app.n8n.cloud")
    fake_client = _FakeAsyncClient()
    monkeypatch.setattr("app.services.n8n.httpx.AsyncClient", lambda **_: fake_client)

    lead_id, clinic_id = uuid.uuid4(), uuid.uuid4()
    await notify_lead_created(lead_id, clinic_id)

    assert fake_client.last_url == "https://example.app.n8n.cloud/webhook/lead.created"
    assert fake_client.last_json == {"lead_id": str(lead_id), "clinic_id": str(clinic_id)}


async def test_notify_appointment_status_changed_dispatches_the_right_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _configure(monkeypatch, n8n_webhook_base_url="https://example.app.n8n.cloud")
    fake_client = _FakeAsyncClient()
    monkeypatch.setattr("app.services.n8n.httpx.AsyncClient", lambda **_: fake_client)

    appointment_id, lead_id, clinic_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    await notify_appointment_status_changed(
        appointment_id=appointment_id,
        lead_id=lead_id,
        clinic_id=clinic_id,
        from_status="pending",
        to_status="booked",
    )

    assert fake_client.last_url == (
        "https://example.app.n8n.cloud/webhook/appointment.status_changed"
    )
    assert fake_client.last_json == {
        "appointment_id": str(appointment_id),
        "lead_id": str(lead_id),
        "clinic_id": str(clinic_id),
        "from_status": "pending",
        "to_status": "booked",
    }
