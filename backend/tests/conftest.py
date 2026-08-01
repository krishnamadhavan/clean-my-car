"""Shared pytest fixtures."""

from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure test-friendly defaults before app settings are loaded
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("OTP_RETURN_IN_RESPONSE", "true")
os.environ.setdefault("OTP_RESEND_COOLDOWN_SECONDS", "0")
os.environ.setdefault("OTP_MAX_REQUESTS_PER_HOUR", "100")


@pytest.fixture
async def client() -> AsyncClient:
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
