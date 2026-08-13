"""Ops subscription schemas (Ops Module 7)."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.subscription import SubscriptionStatus
from app.models.vehicle import VehicleSizeTier
from app.schemas.location import CityOut, SocietySummaryOut


class OpsSubscriptionUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phone: str
    name: str | None = None
    email: str | None = None
    is_active: bool


class OpsSubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    user: OpsSubscriptionUserOut | None = None
    city_id: UUID
    city: CityOut | None = None
    society_id: UUID
    society: SocietySummaryOut | None = None
    vehicle_id: UUID | None = None
    size_tier: VehicleSizeTier
    interior_frequency: int
    status: SubscriptionStatus
    monthly_amount_paise: int
    currency: str
    period_start: date
    period_end: date
    cancel_at: date | None = None
    paused_from: date | None = None
    paused_until: date | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class OpsSubscriptionListOut(BaseModel):
    items: list[OpsSubscriptionOut]
    total: int
    page: int
    page_size: int


class OpsSubscriptionCancelIn(BaseModel):
    """Optional ops note when scheduling admin cancel."""

    model_config = ConfigDict(extra="forbid")

    notes: str | None = Field(default=None, max_length=1000)
