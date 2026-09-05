import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Make `app` importable regardless of how/where `alembic` is invoked from.
sys.path.insert(0, os.getcwd())

from app.core.config import get_settings  # noqa: E402
from app.db.session import _asyncpg_url  # noqa: E402
from app.models import Base  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# DATABASE_URL comes from apps/api/.env (via Settings), never hardcoded in
# alembic.ini, so no secret needs to live in a committed file. Kept out of
# configparser (config.set_main_option) entirely — it uses `%`-interpolation,
# which breaks on a percent-encoded password (e.g. `%40`).
_settings = get_settings()
_database_url = _asyncpg_url(_settings.database_url) if _settings.database_url else None


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    if not _database_url:
        raise RuntimeError("DATABASE_URL is not set — see README.md Supabase setup guide.")
    context.configure(
        url=_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    if not _database_url:
        raise RuntimeError("DATABASE_URL is not set — see README.md Supabase setup guide.")

    connectable = create_async_engine(_database_url, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
