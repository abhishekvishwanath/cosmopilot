"""
Auth-boundary tests for the Vapi-facing webhook router (CLAUDE.md §24),
mirroring test_webhook_auth.py's approach for n8n. The route bodies
(tool-call dispatch, end-of-call-report handling) are exercised via the
mandatory live test call (see the Phase 10 report) rather than duplicated
here with a fake DB — same testing philosophy this file's n8n counterpart
documents.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings

_URL = "/api/v1/webhooks/vapi"


def test_webhook_without_configured_secret_is_unavailable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("VAPI_WEBHOOK_SECRET", raising=False)
    get_settings.cache_clear()

    response = client.post(_URL, json={"message": {"type": "status-update"}})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "vapi_not_configured"


def test_webhook_without_header_is_unauthorized(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VAPI_WEBHOOK_SECRET", "test-secret")
    get_settings.cache_clear()

    response = client.post(_URL, json={"message": {"type": "status-update"}})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_webhook_secret"


def test_webhook_with_wrong_secret_is_unauthorized(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VAPI_WEBHOOK_SECRET", "test-secret")
    get_settings.cache_clear()

    response = client.post(
        _URL, json={"message": {"type": "status-update"}}, headers={"x-vapi-secret": "wrong"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_webhook_secret"
