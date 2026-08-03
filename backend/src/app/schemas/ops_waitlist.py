"""Ops waitlist triage schemas (Ops Module 4)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.waitlist import WaitlistStatus
from app.schemas.location import CityOut


class OpsWaitlistEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None = None
    city_id: UUID
    city: CityOut | None = None
    society_name: str
    phone: str
    notes: str | None = None
    status: WaitlistStatus
    created_at: datetime
    updated_at: datetime


class OpsWaitlistListOut(BaseModel):
    items: list[OpsWaitlistEntryOut]
    total: int
    page: int
    page_size: int


class OpsWaitlistPatch(BaseModel):
    """Update triage fields (OPS-WAIT-03)."""

    model_config = ConfigDict(extra="forbid")

    status: WaitlistStatus | None = None
    notes: str | None = Field(default=None, max_length=1000)
    society_name: str | None = Field(default=None, min_length=1, max_length=200)

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("society_name")
    @classmethod
    def strip_society_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("society_name must not be empty")
        return cleaned


class OpsWaitlistStatusCount(BaseModel):
    status: WaitlistStatus
    count: int


class OpsWaitlistCityCount(BaseModel):
    city_id: UUID
    city_name: str
    count: int


class OpsWaitlistSummaryOut(BaseModel):
    total: int
    by_status: list[OpsWaitlistStatusCount]
    by_city: list[OpsWaitlistCityCount]
