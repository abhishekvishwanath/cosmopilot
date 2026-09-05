from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.db.supabase import DatabaseStatus, check_supabase_connection

router = APIRouter(tags=["health"])


class LivenessResponse(BaseModel):
    status: Literal["ok"] = "ok"
    env: str
    mock_mode: bool


class ReadinessResponse(BaseModel):
    status: Literal["ok", "error"]
    checks: dict[str, DatabaseStatus]


@router.get("/health", response_model=LivenessResponse)
def liveness(settings: Annotated[Settings, Depends(get_settings)]) -> LivenessResponse:
    """Always returns 200 while the process is up — no external calls."""
    return LivenessResponse(env=settings.app_env, mock_mode=settings.mock_mode)


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReadinessResponse:
    """
    Checks dependencies the app actually needs to serve traffic correctly.
    `not_configured` (mock mode, no Supabase project yet) is a valid,
    expected Phase 1 state and still reports overall status "ok" — only a
    configured-but-unreachable dependency is treated as a real failure.
    """
    database = await check_supabase_connection(settings)
    overall: Literal["ok", "error"] = "error" if database.status == "error" else "ok"
    if overall == "error":
        response.status_code = 503
    return ReadinessResponse(status=overall, checks={"database": database})
