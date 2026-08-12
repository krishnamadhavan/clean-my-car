"""Consumer subscription schemas (Module 7)."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.subscription import SubscriptionStatus
from app.models.vehicle import VehicleSizeTier
from app.schemas.location import CityOut, SocietySummaryOut
from app.schemas.pricing import INTERIOR_FREQUENCIES, QuoteOut


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: SubscriptionStatus
    city_id: UUID
    society_id: UUID
    vehicle_id: UUID | None = None
    size_tier: VehicleSizeTier
    interior_frequency: int
    monthly_amount_paise: int
    currency: str
    period_start: date
    period_end: date
    cancel_at: date | None = None
    paused_from: date | None = None
    paused_until: date | None = None
    city: CityOut | None = None
    society: SocietySummaryOut | None = None
    created_at: datetime
    updated_at: datetime


class SubscriptionStartIn(BaseModel):
    """POST /me/subscription — start after location + vehicle are set."""

    model_config = ConfigDict(extra="forbid")

    interior_frequency: int = Field(description="0, 1, 2, or 4 cleans per month")
    start_date: date | None = Field(
        default=None,
        description="Service start (defaults to today Asia/Kolkata).",
    )

    @field_validator("interior_frequency")
    @classmethod
    def validate_interior_frequency(cls, value: int) -> int:
        if value not in INTERIOR_FREQUENCIES:
            raise ValueError("interior_frequency must be one of 0, 1, 2, 4")
        return value


class SubscriptionStartOut(BaseModel):
    """Start response: subscription + first payment intent to complete."""

    subscription: SubscriptionOut
    payment_intent_id: UUID
    amount_due_now_paise: int
    currency: str
    quote: QuoteOut
