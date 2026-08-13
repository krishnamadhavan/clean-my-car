"""Ops wash schemas (OPS-WASH-*)."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.wash import WashStatus


class OpsWashOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    subscription_id: UUID
    society_id: UUID
    vehicle_id: UUID | None = None
    service_date: date
    status: WashStatus
    includes_exterior: bool
    includes_interior: bool
    completed_at: datetime | None = None
    completed_by_operator_id: UUID | None = None
    miss_reason: str | None = None
    retry_of_wash_id: UUID | None = None
    notes: str | None = None
    user_phone: str | None = None
    user_name: str | None = None
    society_name: str | None = None
    created_at: datetime
    updated_at: datetime


class OpsWashListOut(BaseModel):
    items: list[OpsWashOut]
    total: int
    page: int
    page_size: int


class OpsWashCompleteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    includes_interior: bool = False
    notes: str | None = Field(default=None, max_length=1000)


class OpsWashMissIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=500)
    schedule_retry: bool = True
    notes: str | None = Field(default=None, max_length=1000)


class OpsWashGenerateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    society_id: UUID | None = None
    subscription_id: UUID | None = None
    from_date: date | None = None
    until_date: date | None = None


class OpsWashGenerateOut(BaseModel):
    created: int
    skipped_existing: int
    message: str


class OpsRosterItemOut(BaseModel):
    wash_id: UUID
    user_id: UUID
    user_phone: str
    user_name: str | None
    vehicle_id: UUID | None
    service_date: date
    status: WashStatus
    includes_exterior: bool
    includes_interior: bool
    subscription_id: UUID


class OpsRosterOut(BaseModel):
    society_id: UUID
    society_name: str
    service_date: date
    items: list[OpsRosterItemOut]
    total: int
