"""Shared pytest fixtures and ephemeral test database lifecycle.

Tests use database ``cleanmycar_test`` (override with ``POSTGRES_TEST_DB``).
That database is created and migrated before the suite runs, and dropped after.
The long-running app continues to use ``cleanmycar`` / ``POSTGRES_APP_DB``.
"""

from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

# Configure env + create DB *before* any test module imports ``app`` (collection).
# pytest loads conftest first, then runs pytest_configure, then collects tests.
from tests.db_lifecycle import (
    configure_test_database_env,
    setup_test_database,
    teardown_test_database,
)

configure_test_database_env()

# Test-friendly defaults (do not override DATABASE_URL set above)
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("OTP_RETURN_IN_RESPONSE", "true")
os.environ.setdefault("OTP_RESEND_COOLDOWN_SECONDS", "0")
os.environ.setdefault("OTP_MAX_REQUESTS_PER_HOUR", "100")
# Never bootstrap ops operators during tests (would race with suite isolation)
os.environ.setdefault("OPS_BOOTSTRAP_EMAIL", "")
os.environ.setdefault("OPS_BOOTSTRAP_PASSWORD", "")


def pytest_configure(config: pytest.Config) -> None:
    """Create ephemeral DB and run migrations before test collection imports the app."""
    setup_test_database()


def pytest_unconfigure(config: pytest.Config) -> None:
    """Drop the ephemeral test database after the entire suite finishes."""
    teardown_test_database()


@pytest.fixture
async def client() -> AsyncClient:
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
