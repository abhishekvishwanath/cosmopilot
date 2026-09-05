import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings


def test_liveness_always_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "env" in body
    assert "mock_mode" in body


def test_readiness_reports_not_configured_without_supabase_env(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    get_settings.cache_clear()

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"]["status"] == "not_configured"


def test_readiness_reports_error_on_unreachable_supabase_url(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPABASE_URL", "https://this-project-does-not-exist.invalid")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-key")
    get_settings.cache_clear()

    response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["checks"]["database"]["status"] == "error"
