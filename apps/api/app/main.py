import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, log_with_fields

logger = logging.getLogger("cosmopilot.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging()
    log_with_fields(
        logger,
        logging.INFO,
        "startup",
        env=settings.app_env,
        mock_mode=settings.mock_mode,
        supabase_configured=settings.supabase_configured,
        auth_configured=settings.auth_configured,
    )
    yield
    log_with_fields(logger, logging.INFO, "shutdown")


app = FastAPI(title="CosmoPilot API", version="0.1.0", lifespan=lifespan)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.app_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    log_with_fields(
        logger,
        logging.INFO,
        "request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


def _error_body(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or {}}}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    # Routes that already raise a structured {"error": {...}} detail (see
    # app/core/security.py) pass straight through; anything else (404s,
    # framework-raised errors) is normalized to the same shape — see
    # docs/API_CONVENTIONS.md.
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        body = exc.detail
    else:
        body = _error_body(f"http_{exc.status_code}", str(exc.detail))
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            _error_body(
                "validation_error", "Request validation failed.", {"errors": exc.errors()}
            )
        ),
    )


app.include_router(api_router, prefix="/api/v1")
