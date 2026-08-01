"""Cryptographic helpers: OTP hashing, JWT, refresh token hashing."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt

from app.core.config import Settings


def generate_otp(length: int = 6) -> str:
    """Numeric OTP of fixed length (cryptographically strong)."""
    upper = 10**length
    return str(secrets.randbelow(upper)).zfill(length)


def hash_otp(otp: str, *, secret: str) -> str:
    return hmac.new(secret.encode(), otp.encode(), hashlib.sha256).hexdigest()


def verify_otp(otp: str, otp_hash: str, *, secret: str) -> bool:
    expected = hash_otp(otp, secret=secret)
    return hmac.compare_digest(expected, otp_hash)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(
    *,
    subject: UUID,
    settings: Settings,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": "access",
        "iat": now,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, *, settings: Settings) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "sub", "type"]},
    )
