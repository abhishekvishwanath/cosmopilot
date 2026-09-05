from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings


class AuthError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(
            status_code=status_code,
            detail={"error": {"code": code, "message": message, "details": {}}},
        )


@lru_cache
def _jwks_client(supabase_url: str) -> jwt.PyJWKClient:
    # cache_jwk_set (default True) keeps the fetched key set for `lifespan`
    # seconds (default 300) inside this client instance — lru_cache keeps
    # one instance alive per project URL so that caching actually applies
    # across requests instead of refetching the JWKS every time.
    return jwt.PyJWKClient(f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json")


def decode_supabase_jwt(token: str, settings: Settings) -> dict[str, Any]:
    """
    Verify a Supabase Auth access token.

    Supabase projects created with the newer "JWT Signing Keys" (the
    current default) issue asymmetric tokens (ES256/RS256) — these are
    verified via the project's JWKS endpoint, with no shared secret needed.
    Older projects still on the legacy HS256 shared secret
    (SUPABASE_JWT_SECRET, Project Settings -> API -> JWT Settings) are
    supported as a fallback when no JWKS key matches.

    This is the deterministic authorization check CLAUDE.md requires — the
    LLM/agents never decide who a request is authenticated as.
    """
    if not settings.auth_configured:
        raise AuthError(
            "auth_not_configured",
            "Supabase is not configured — authentication is unavailable until "
            "SUPABASE_URL (and/or SUPABASE_JWT_SECRET) is set (see README.md "
            "Supabase setup guide).",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    if settings.supabase_url:
        try:
            signing_key = _jwks_client(settings.supabase_url).get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                audience="authenticated",
            )
        except jwt.PyJWKClientError:
            # No matching key in the JWKS — fall through to the legacy
            # secret below, e.g. for a project still on HS256 (whose
            # symmetric key is never published via JWKS).
            pass
        except jwt.ExpiredSignatureError as exc:
            raise AuthError("token_expired", "The access token has expired.") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthError("invalid_token", "The access token is invalid.") from exc

    if settings.supabase_jwt_secret:
        try:
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthError("token_expired", "The access token has expired.") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthError("invalid_token", "The access token is invalid.") from exc

    raise AuthError(
        "invalid_token",
        "The access token could not be verified against the project's JWKS or "
        "the legacy JWT secret.",
    )


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("unauthorized", "Missing or malformed Authorization header.")
    return authorization.split(" ", 1)[1].strip()


def get_current_user(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """
    FastAPI dependency: resolves the authenticated Supabase user from a
    `Authorization: Bearer <token>` header. Clinic-scoped authorization
    (matching the user to a clinic_id) is added in Phase 2 once the
    clinics/staff tables exist — this dependency only proves *who* the
    caller is, per CLAUDE.md's deterministic-authorization requirement.
    """
    token = _extract_bearer_token(authorization)
    return decode_supabase_jwt(token, settings)
