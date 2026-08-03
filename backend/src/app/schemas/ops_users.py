"""Ops user support schemas (Ops Module 2)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.location import CityOut, SocietySummaryOut


class OpsUserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phone: str
    name: str | None = None
    email: str | None = None
    is_active: bool
    deleted_at: datetime | None = None
    city_id: UUID | None = None
    society_id: UUID | None = None
    created_at: datetime


class OpsUserDetail(OpsUserSummary):
    city: CityOut | None = None
    society: SocietySummaryOut | None = None
    has_vehicle: bool = False
    has_subscription: bool = False
    updated_at: datetime


class OpsUserListOut(BaseModel):
    items: list[OpsUserSummary]
    total: int
    page: int
    page_size: int


class OpsMessageOut(BaseModel):
    message: str
