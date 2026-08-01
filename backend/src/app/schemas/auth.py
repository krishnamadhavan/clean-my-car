"""Auth request/response schemas (Module 1)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.user import UserPublic


class OtpRequestIn(BaseModel):
    phone: str = Field(..., examples=["9876543210", "+919876543210"])


class OtpRequestOut(BaseModel):
    message: str = "OTP sent"
    phone: str
    expires_at: datetime
    resend_available_at: datetime
    # Present only when OTP_RETURN_IN_RESPONSE is enabled (development)
    debug_otp: str | None = None


class OtpVerifyIn(BaseModel):
    phone: str
    otp: str = Field(..., min_length=4, max_length=8, pattern=r"^\d+$")


class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token lifetime in seconds
    user: UserPublic


class RefreshTokenIn(BaseModel):
    refresh_token: str


class AccessTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str | None = None  # rotated refresh token when issued


class LogoutIn(BaseModel):
    refresh_token: str


class MessageOut(BaseModel):
    message: str


class ErrorOut(BaseModel):
    code: str
    message: str
    details: dict | list | None = None


class AuthSessionOut(BaseModel):
    """Could-priority AUTH-05 — not implemented in v1 Must set."""

    user_id: UUID
    phone: str
