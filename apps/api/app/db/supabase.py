from typing import Literal

import httpx
from pydantic import BaseModel

from app.core.config import Settings

DatabaseStatusValue = Literal["ok", "not_configured", "error"]


class DatabaseStatus(BaseModel):
    status: DatabaseStatusValue
    detail: str | None = None


async def check_supabase_connection(settings: Settings) -> DatabaseStatus:
    """
    Confirms the Supabase project is reachable and the configured API key is
    accepted, without requiring any application table to exist yet (Phase 2
    adds those). Hits PostgREST's root endpoint.

    Prefers SUPABASE_SERVICE_ROLE_KEY when set: PostgREST restricts this
    introspection endpoint's full schema response to service_role, and
    rejects the anon key here with a 401 ("Only the service_role API key can
    be used for this endpoint") even when the anon key is perfectly valid.
    If only the anon key is configured, that specific rejection is treated
    as a successful reachability check rather than an error, to avoid a
    false "error" status for a valid but anon-only configuration.
    """
    if not settings.supabase_configured:
        return DatabaseStatus(
            status="not_configured",
            detail="SUPABASE_URL / SUPABASE_ANON_KEY not set — running in mock mode.",
        )

    # supabase_configured guarantees both are set; assert narrows the type for mypy.
    assert settings.supabase_url and settings.supabase_anon_key

    using_service_role = bool(settings.supabase_service_role_key)
    key = settings.supabase_service_role_key or settings.supabase_anon_key

    url = f"{settings.supabase_url.rstrip('/')}/rest/v1/"
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        return DatabaseStatus(
            status="error",
            detail=f"Could not reach Supabase at SUPABASE_URL: {exc.__class__.__name__}.",
        )

    if response.status_code == 200:
        return DatabaseStatus(status="ok", detail=None)

    if response.status_code in (401, 403):
        if not using_service_role and "service_role" in response.text:
            return DatabaseStatus(
                status="ok",
                detail=(
                    "Reachable — SUPABASE_ANON_KEY accepted. Set SUPABASE_SERVICE_ROLE_KEY "
                    "for a full schema-introspection check."
                ),
            )
        key_name = "SUPABASE_SERVICE_ROLE_KEY" if using_service_role else "SUPABASE_ANON_KEY"
        return DatabaseStatus(
            status="error",
            detail=f"Supabase rejected the API key — check {key_name}.",
        )

    if response.status_code >= 500:
        return DatabaseStatus(
            status="error",
            detail=f"Supabase returned a server error (HTTP {response.status_code}).",
        )

    return DatabaseStatus(status="ok", detail=None)
