import time

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings

TEST_SECRET = "test-jwt-secret-at-least-32-bytes-long"


def _token(secret: str = TEST_SECRET, **overrides: object) -> str:
    payload = {
        "sub": "00000000-0000-0000-0000-000000000000",
        "email": "patient@example.com",
        "role": "authenticated",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
        **overrides,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def test_me_without_header_is_unauthorized(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPABASE_JWT_SECRET", TEST_SECRET)
    get_settings.cache_clear()

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_me_without_configured_secret_is_unavailable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)
    get_settings.cache_clear()

    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {_token()}"}
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "auth_not_configured"


def test_me_with_valid_token_returns_claims(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPABASE_JWT_SECRET", TEST_SECRET)
    get_settings.cache_clear()

    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {_token()}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "patient@example.com"
    assert body["aud"] == "authenticated"


def test_me_with_wrong_signature_is_invalid(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SUPABASE_JWT_SECRET", TEST_SECRET)
    get_settings.cache_clear()

    bad_token = _token(secret="wrong-secret")
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {bad_token}"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_token"
