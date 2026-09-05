from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings, get_settings


def _asyncpg_url(database_url: str) -> str:
    """Accepts the standard `postgresql://` URL Supabase shows in its
    dashboard and adapts it for SQLAlchemy's async engine (asyncpg driver)."""
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


@lru_cache
def _engine_for(database_url: str) -> AsyncEngine:
    return create_async_engine(_asyncpg_url(database_url), pool_pre_ping=True)


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    settings = settings or get_settings()
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is not set — see README.md Supabase setup guide."
        )
    return _engine_for(settings.database_url)


def get_sessionmaker(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(settings), expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a request-scoped AsyncSession."""
    session_factory = get_sessionmaker()
    async with session_factory() as session:
        yield session
