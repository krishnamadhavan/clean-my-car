"""Ops auth request/response schemas (Ops Module 1)."""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class OpsOperatorPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str | None = None
    is_active: bool
    roles: list[str] = Field(default_factory=list)
    last_login_at: datetime | None = None
    created_at: datetime


class OpsLoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not _EMAIL_RE.match(cleaned):
            raise ValueError("Invalid email address")
        return cleaned


class OpsTokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    operator: OpsOperatorPublic


class OpsAccessTokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class OpsRefreshIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(..., min_length=20)


class OpsLogoutIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(..., min_length=20)


class OpsMessageOut(BaseModel):
    message: str
