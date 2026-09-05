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


def decode_supabase_jwt(token: str, settings: Settings) -> dict[str, Any]:
    """
    Verify a Supabase Auth access token using the project's JWT secret
    (Project Settings -> API -> JWT Settings in the Supabase dashboard).

    Supabase issues HS256 tokens with `aud="authenticated"` for logged-in
    users. This is the deterministic authorization check CLAUDE.md requires —
    the LLM/agents never decide who a request is authenticated as.
    """
    if not settings.auth_configured:
        raise AuthError(
            "auth_not_configured",
            "SUPABASE_JWT_SECRET is not set — authentication is unavailable until "
            "Supabase is configured (see README.md Supabase setup guide).",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

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
