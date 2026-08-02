"""Waitlist schemas (Module 4)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.waitlist import WaitlistStatus
from app.schemas.location import CityOut


class WaitlistCreate(BaseModel):
    """POST /waitlist body (WAIT-01).

    ``phone`` is required when the caller is not authenticated; authenticated
    callers may omit it (defaults to their account phone).
    """

    city_id: UUID
    society_name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("society_name")
    @classmethod
    def strip_society_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Society name is required")
        return cleaned

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class WaitlistEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    city_id: UUID
    city: CityOut | None = None
    society_name: str
    phone: str
    notes: str | None = None
    status: WaitlistStatus
    created_at: datetime
    updated_at: datetime


class WaitlistListOut(BaseModel):
    items: list[WaitlistEntryOut]
