"""Pricing schemas (Module 6)."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.vehicle import VehicleSizeTier
from app.schemas.location import CityOut, SocietySummaryOut

# Allowed interior package frequencies (cleans per calendar month)
INTERIOR_FREQUENCIES = (0, 1, 2, 4)


class InteriorOptionOut(BaseModel):
    frequency: int
    code: str
    label: str
    description: str


class InteriorOptionsOut(BaseModel):
    items: list[InteriorOptionOut]


class SizePriceOut(BaseModel):
    size_tier: VehicleSizeTier
    monthly_amount_paise: int


class InteriorPriceOut(BaseModel):
    interior_frequency: int
    monthly_amount_paise: int


class CityPricingOut(BaseModel):
    """GET /cities/{city_id}/pricing (PRICE-01)."""

    city: CityOut
    currency: str
    amounts_include_gst: bool
    gst_rate_bps: int
    size_prices: list[SizePriceOut]
    interior_prices: list[InteriorPriceOut]
    # Convenience matrix: size × frequency → total monthly (base + interior)
    matrix: list[PricingMatrixCellOut]


class PricingMatrixCellOut(BaseModel):
    size_tier: VehicleSizeTier
    interior_frequency: int
    base_amount_paise: int
    interior_amount_paise: int
    monthly_total_paise: int


class QuoteIn(BaseModel):
    """POST /pricing/quote body (PRICE-02)."""

    model_config = ConfigDict(extra="forbid")

    city_id: UUID
    size_tier: VehicleSizeTier
    interior_frequency: int = Field(description="0, 1, 2, or 4 cleans per month")
    start_date: date | None = Field(
        default=None,
        description="Service start date (calendar). Defaults to today in Asia/Kolkata.",
    )
    society_id: UUID | None = Field(
        default=None,
        description="Optional live society for service-day entitlement preview.",
    )

    @field_validator("interior_frequency")
    @classmethod
    def validate_interior_frequency(cls, value: int) -> int:
        if value not in INTERIOR_FREQUENCIES:
            raise ValueError("interior_frequency must be one of 0, 1, 2, 4")
        return value


class MoneyBreakdownOut(BaseModel):
    base_amount_paise: int
    gst_paise: int
    total_paise: int


class QuoteOut(BaseModel):
    city: CityOut
    size_tier: VehicleSizeTier
    interior_frequency: int
    currency: str
    amounts_include_gst: bool
    gst_rate_bps: int

    # Full calendar-month list price (size base + interior add-on)
    full_monthly_base_paise: int
    full_monthly_interior_paise: int
    full_monthly_total_paise: int
    full_monthly_breakdown: MoneyBreakdownOut

    # Amount due for remainder of start month (pro-rated)
    start_date: date
    billing_month: str  # e.g. "2026-08"
    days_in_month: int
    remaining_days: int
    amount_due_now_paise: int
    amount_due_now_breakdown: MoneyBreakdownOut
    is_prorated: bool

    # Next full month
    next_billing_month: str
    next_full_month_amount_paise: int

    # Entitlement preview for remainder of start month
    exterior_entitled_this_period: int | None = None
    exterior_entitled_full_month: int | None = None
    interior_entitled_this_period: int
    interior_entitled_full_month: int

    society: SocietySummaryOut | None = None
    service_weekdays: list[int] | None = None
    service_weekday_labels: list[str] | None = None
    pro_rate_method: str = "calendar_days"
