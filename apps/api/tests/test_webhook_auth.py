"""
Auth-boundary tests for the n8n-facing webhook router (CLAUDE.md §24 — every
webhook needs verification). These only exercise the auth dependency's
failure paths — it raises before the route ever touches the database (see
app/core/security.py::verify_n8n_webhook), so no DB fixture is needed here,
same reasoning as test_auth.py's JWT tests. The route bodies themselves
were verified live against the real Supabase project (see the Phase 8
report) — this suite's job is only to guard the security boundary.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings

_ANY_ID = str(uuid.uuid4())
_URL = f"/api/v1/webhooks/n8n/leads/{_ANY_ID}?clinic_id={_ANY_ID}"


def test_webhook_without_configured_secret_is_unavailable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("N8N_WEBHOOK_SHARED_SECRET", raising=False)
    get_settings.cache_clear()

    response = client.get(_URL)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "n8n_not_configured"


def test_webhook_without_header_is_unauthorized(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("N8N_WEBHOOK_SHARED_SECRET", "test-shared-secret")
    get_settings.cache_clear()

    response = client.get(_URL)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_webhook_secret"


def test_webhook_with_wrong_secret_is_unauthorized(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("N8N_WEBHOOK_SHARED_SECRET", "test-shared-secret")
    get_settings.cache_clear()

    response = client.get(_URL, headers={"X-Webhook-Secret": "wrong-secret"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_webhook_secret"
