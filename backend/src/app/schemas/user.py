"""User / profile request and response schemas."""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phone: str
    name: str | None = None
    email: str | None = None
    is_active: bool
    created_at: datetime


class MeOut(UserPublic):
    """GET /me — profile plus high-level account flags (PROF-01)."""

    has_vehicle: bool = False
    has_subscription: bool = False
    deleted_at: datetime | None = None


class MeUpdate(BaseModel):
    """PATCH /me — only provided fields are updated (PROF-02).

    Send JSON ``null`` for a field to clear it.
    """

    name: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=255)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if not cleaned:
            return None
        if not _EMAIL_RE.match(cleaned):
            raise ValueError("Invalid email address")
        return cleaned


class MessageOut(BaseModel):
    message: str
