"""Create / migrate / drop an ephemeral PostgreSQL database for pytest.

The application continues to use the normal ``cleanmycar`` (or ``POSTGRES_DB``)
database. Tests use ``POSTGRES_TEST_DB`` (default ``cleanmycar_test``), which is
created at session start and dropped at session end.
"""

from __future__ import annotations

import asyncio
import os
from urllib.parse import quote_plus

import asyncpg
from alembic import command
from alembic.config import Config

DEFAULT_TEST_DB = "cleanmycar_test"
# Maintenance DB for CREATE/DROP DATABASE (must already exist)
ADMIN_DB = "postgres"


def test_db_name() -> str:
    return os.environ.get("POSTGRES_TEST_DB", DEFAULT_TEST_DB)


def _pg_parts() -> tuple[str, str, str, int]:
    user = os.environ.get("POSTGRES_USER", "cleanmycar")
    password = os.environ.get("POSTGRES_PASSWORD", "cleanmycar")
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))
    return user, password, host, port


def configure_test_database_env() -> str:
    """Point process env at the ephemeral test DB (call before importing app)."""
    user, password, host, port = _pg_parts()
    name = test_db_name()
    # Never allow tests to target the primary app DB name by accident
    app_db = os.environ.get("POSTGRES_APP_DB", "cleanmycar")
    if name == app_db:
        name = DEFAULT_TEST_DB

    url = f"postgresql+asyncpg://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{name}"
    os.environ["APP_ENV"] = "test"
    os.environ["POSTGRES_DB"] = name
    os.environ["DATABASE_URL"] = url
    return name


async def _admin_connection() -> asyncpg.Connection:
    user, password, host, port = _pg_parts()
    return await asyncpg.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=ADMIN_DB,
    )


async def create_test_database() -> None:
    name = test_db_name()
    conn = await _admin_connection()
    try:
        # Terminate leftovers and recreate for a clean slate
        await conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        await conn.execute(f'CREATE DATABASE "{name}"')
    finally:
        await conn.close()


async def drop_test_database() -> None:
    name = test_db_name()
    conn = await _admin_connection()
    try:
        await conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
    finally:
        await conn.close()


def run_alembic_upgrade() -> None:
    """Apply migrations to the DB currently set in ``DATABASE_URL`` / settings."""
    # Clear cached settings so Alembic picks up the test URL
    from app.core.config import get_settings

    get_settings.cache_clear()
    # alembic.ini lives in backend/ (cwd for make test and CI)
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")


async def dispose_app_engine_if_loaded() -> None:
    """Close SQLAlchemy pools so DROP DATABASE is not blocked."""
    try:
        from app.db import session as sess
    except ImportError:
        return
    await sess.dispose_engine()


def setup_test_database() -> None:
    configure_test_database_env()
    asyncio.run(create_test_database())
    run_alembic_upgrade()


def teardown_test_database() -> None:
    try:
        asyncio.run(dispose_app_engine_if_loaded())
    except Exception:  # noqa: BLE001 — best-effort dispose before drop
        pass
    asyncio.run(drop_test_database())
