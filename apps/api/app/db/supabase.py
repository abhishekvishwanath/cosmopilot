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
    Confirms the Supabase project is reachable and the anon key is accepted,
    without requiring any application table to exist yet (Phase 2 adds
    those). Hits PostgREST's root endpoint, which responds for any valid
    project + API key.
    """
    if not settings.supabase_configured:
        return DatabaseStatus(
            status="not_configured",
            detail="SUPABASE_URL / SUPABASE_ANON_KEY not set — running in mock mode.",
        )

    # supabase_configured above guarantees both are set; assert narrows the type for mypy.
    assert settings.supabase_url and settings.supabase_anon_key

    url = f"{settings.supabase_url.rstrip('/')}/rest/v1/"
    headers = {
        "apikey": settings.supabase_anon_key,
        "Authorization": f"Bearer {settings.supabase_anon_key}",
    }

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url, headers=headers)
    except httpx.RequestError as exc:
        return DatabaseStatus(
            status="error",
            detail=f"Could not reach Supabase at SUPABASE_URL: {exc.__class__.__name__}.",
        )

    if response.status_code in (401, 403):
        return DatabaseStatus(
            status="error",
            detail="Supabase rejected the API key — check SUPABASE_ANON_KEY.",
        )
    if response.status_code >= 500:
        return DatabaseStatus(
            status="error",
            detail=f"Supabase returned a server error (HTTP {response.status_code}).",
        )

    return DatabaseStatus(status="ok", detail=None)
