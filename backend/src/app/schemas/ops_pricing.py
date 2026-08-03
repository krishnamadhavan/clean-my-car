"""Ops pricing catalog schemas (Ops Module 6)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.vehicle import VehicleSizeTier
from app.schemas.ops_location import OpsCityOut
from app.schemas.pricing import INTERIOR_FREQUENCIES, PricingMatrixCellOut, QuoteIn, QuoteOut

# Re-export for ops endpoints / OpenAPI convenience
__all__ = [
    "OpsCityPricingOut",
    "OpsCityPricingPut",
    "OpsInteriorPriceItem",
    "OpsInteriorPricesPut",
    "OpsMissingPricingListOut",
    "OpsMissingPricingOut",
    "OpsSizePriceItem",
    "OpsSizePricesPut",
    "QuoteIn",
    "QuoteOut",
]


class OpsSizePriceOut(BaseModel):
    size_tier: VehicleSizeTier
    monthly_amount_paise: int


class OpsInteriorPriceOut(BaseModel):
    interior_frequency: int
    monthly_amount_paise: int


class OpsCityPricingOut(BaseModel):
    """Full ops view of city pricing (OPS-PRICE-01)."""

    id: UUID
    city_id: UUID
    city: OpsCityOut
    currency: str
    amounts_include_gst: bool
    gst_rate_bps: int
    is_active: bool
    size_prices: list[OpsSizePriceOut]
    interior_prices: list[OpsInteriorPriceOut]
    matrix: list[PricingMatrixCellOut]
    created_at: datetime
    updated_at: datetime


class OpsCityPricingPut(BaseModel):
    """Upsert city pricing config (OPS-PRICE-02). Does not replace price rows."""

    model_config = ConfigDict(extra="forbid")

    currency: str = Field(default="INR", min_length=3, max_length=3)
    amounts_include_gst: bool = True
    gst_rate_bps: int = Field(default=1800, ge=0, le=10000)
    is_active: bool = True

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        cleaned = value.strip().upper()
        if len(cleaned) != 3 or not cleaned.isalpha():
            raise ValueError("currency must be a 3-letter ISO code")
        return cleaned


class OpsSizePriceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    size_tier: VehicleSizeTier
    monthly_amount_paise: int = Field(..., ge=0)


class OpsSizePricesPut(BaseModel):
    """Replace size-tier base prices (OPS-PRICE-03). Full replace of the set."""

    model_config = ConfigDict(extra="forbid")

    items: list[OpsSizePriceItem] = Field(..., min_length=1)

    @model_validator(mode="after")
    def unique_tiers(self) -> OpsSizePricesPut:
        tiers = [item.size_tier for item in self.items]
        if len(tiers) != len(set(tiers)):
            raise ValueError("size_tier values must be unique")
        return self


class OpsInteriorPriceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interior_frequency: int
    monthly_amount_paise: int = Field(..., ge=0)

    @field_validator("interior_frequency")
    @classmethod
    def validate_frequency(cls, value: int) -> int:
        if value not in INTERIOR_FREQUENCIES:
            raise ValueError("interior_frequency must be one of 0, 1, 2, 4")
        return value


class OpsInteriorPricesPut(BaseModel):
    """Replace interior add-on prices (OPS-PRICE-04). Full replace of the set."""

    model_config = ConfigDict(extra="forbid")

    items: list[OpsInteriorPriceItem] = Field(..., min_length=1)

    @model_validator(mode="after")
    def unique_frequencies(self) -> OpsInteriorPricesPut:
        freqs = [item.interior_frequency for item in self.items]
        if len(freqs) != len(set(freqs)):
            raise ValueError("interior_frequency values must be unique")
        return self


class OpsMissingPricingOut(BaseModel):
    city: OpsCityOut
    has_inactive_pricing: bool = False


class OpsMissingPricingListOut(BaseModel):
    items: list[OpsMissingPricingOut]
    total: int
