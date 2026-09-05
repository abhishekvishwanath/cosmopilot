from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from app.core.config import Settings
from app.core.security import AuthError, decode_supabase_jwt


class _FakeSigningKey:
    def __init__(self, key: Any):
        self.key = key


class _FakeJWKSClient:
    def __init__(self, key: Any | None):
        self._key = key

    def get_signing_key_from_jwt(self, token: str) -> _FakeSigningKey:
        if self._key is None:
            raise jwt.PyJWKClientError("no matching key for kid")
        return _FakeSigningKey(self._key)


def _claims(**overrides: Any) -> dict[str, Any]:
    now = datetime.now(UTC)
    return {
        "sub": "00000000-0000-0000-0000-000000000000",
        "email": "patient@example.com",
        "role": "authenticated",
        "aud": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        **overrides,
    }


def test_jwks_path_verifies_real_asymmetric_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mirrors what a real Supabase project using JWT Signing Keys issues (ES256)."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    token = jwt.encode(_claims(), private_key, algorithm="ES256")

    monkeypatch.setattr(
        "app.core.security._jwks_client", lambda url: _FakeJWKSClient(public_key)
    )
    settings = Settings(supabase_url="https://example.supabase.co")

    claims = decode_supabase_jwt(token, settings)

    assert claims["email"] == "patient@example.com"


def test_jwks_no_matching_key_falls_back_to_legacy_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "legacy-secret-at-least-32-bytes-long"
    token = jwt.encode(_claims(email="legacy@example.com"), secret, algorithm="HS256")

    monkeypatch.setattr("app.core.security._jwks_client", lambda url: _FakeJWKSClient(None))
    settings = Settings(supabase_url="https://example.supabase.co", supabase_jwt_secret=secret)

    claims = decode_supabase_jwt(token, settings)

    assert claims["email"] == "legacy@example.com"


def test_jwks_no_match_and_no_legacy_secret_is_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    token = jwt.encode(_claims(), private_key, algorithm="ES256")

    monkeypatch.setattr("app.core.security._jwks_client", lambda url: _FakeJWKSClient(None))
    settings = Settings(supabase_url="https://example.supabase.co")

    with pytest.raises(AuthError):
        decode_supabase_jwt(token, settings)
