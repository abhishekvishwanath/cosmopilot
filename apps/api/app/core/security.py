import hmac
import logging
import uuid
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated, Any

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.clinic import ClinicStaff


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


@dataclass(frozen=True)
class ClinicPrincipal:
    """The authenticated caller, resolved to a specific clinic via
    `clinic_staff` — this is what every clinic-scoped route depends on."""

    user_id: uuid.UUID
    email: str | None
    clinic_id: uuid.UUID
    role: str


async def get_current_clinic_staff(
    user: Annotated[dict[str, Any], Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicPrincipal:
    """
    Resolves the JWT-authenticated user to the clinic they're staff of.
    This is the clinic-scoped authorization CLAUDE.md §23 requires — every
    clinic-scoped route depends on this instead of a bare authenticated
    user, so a request can never act on a clinic the caller doesn't belong
    to (defense in depth alongside the RLS policies in the migrations).

    A prototype user belongs to exactly one clinic; multi-clinic staff
    accounts are out of scope until a real need for them shows up.
    """
    try:
        user_id = uuid.UUID(str(user.get("sub")))
    except (ValueError, TypeError) as exc:
        raise AuthError("invalid_token", "Token subject is not a valid user id.") from exc

    result = await db.execute(select(ClinicStaff).where(ClinicStaff.user_id == user_id))
    staff = result.scalars().first()
    if staff is None:
        raise AuthError(
            "no_clinic_access",
            "This account is not linked to any clinic.",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    return ClinicPrincipal(
        user_id=user_id, email=user.get("email"), clinic_id=staff.clinic_id, role=staff.role
    )


def verify_n8n_webhook(
    settings: Annotated[Settings, Depends(get_settings)],
    x_webhook_secret: Annotated[str | None, Header()] = None,
) -> None:
    """
    Authenticates n8n's own calls into `/api/v1/webhooks/n8n/*` (CLAUDE.md
    §24 — every webhook needs verification). n8n's HTTP Request node
    doesn't do request signing the way Meta/Stripe/Vapi webhooks will
    (Phase 9/10), so a static shared-secret header is the pragmatic
    equivalent at this trust boundary; those later integrations get real
    signature verification when they land.
    """
    if not settings.n8n_webhook_shared_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "n8n_not_configured",
                    "message": "N8N_WEBHOOK_SHARED_SECRET is not set.",
                    "details": {},
                }
            },
        )
    if not x_webhook_secret or not hmac.compare_digest(
        x_webhook_secret, settings.n8n_webhook_shared_secret
    ):
        raise AuthError("invalid_webhook_secret", "Missing or invalid X-Webhook-Secret header.")


def verify_vapi_webhook(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    x_vapi_secret: Annotated[str | None, Header()] = None,
) -> None:
    """
    Authenticates Vapi's own calls into `/api/v1/webhooks/vapi` (CLAUDE.md
    §24). Vapi is configured (scripts/create_vapi_assistant.py) with a
    `server.secret` that it's documented to echo back on an `x-vapi-secret`
    header — verified against real account data (an existing assistant on
    this Vapi account) but not yet confirmed against Vapi's current public
    docs, since those pages 404'd during Phase 10 research. Logs every
    header on a mismatch (never the correct secret itself) so the real
    header name is visible from the first live test call if this guess
    turns out wrong — but always fails closed either way; nothing here
    ever bypasses verification.
    """
    if not settings.vapi_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "vapi_not_configured",
                    "message": "VAPI_WEBHOOK_SECRET is not set.",
                    "details": {},
                }
            },
        )
    if not x_vapi_secret or not hmac.compare_digest(x_vapi_secret, settings.vapi_webhook_secret):
        logging.getLogger("cosmopilot.webhooks.vapi").warning(
            "vapi_webhook_secret_header_mismatch headers=%s",
            {k: v for k, v in request.headers.items() if "secret" not in k.lower()},
        )
        raise AuthError("invalid_webhook_secret", "Missing or invalid x-vapi-secret header.")
