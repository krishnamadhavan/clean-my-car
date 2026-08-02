"""Vehicle schemas (Module 5) — make/model catalog; size derived server-side."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.plate import normalize_indian_plate
from app.models.vehicle import VehicleSizeTier


class VehicleMakeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    display_order: int


class VehicleModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    make_id: UUID
    name: str
    size_tier: VehicleSizeTier
    display_order: int


class VehicleModelListOut(BaseModel):
    items: list[VehicleModelOut]


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    model_id: UUID
    make: VehicleMakeOut | None = None
    model: VehicleModelOut | None = None
    size_tier: VehicleSizeTier
    nickname: str | None = None
    plate_number: str | None = None
    colour: str | None = None
    parking_slot: str | None = None
    parking_tower: str | None = None
    created_at: datetime
    updated_at: datetime


class VehiclePut(BaseModel):
    """PUT /me/vehicle — create or full replace (VEH-02).

    Size tier is **not** accepted; it is derived from ``model_id``.
    """

    model_config = ConfigDict(extra="forbid")

    model_id: UUID
    nickname: str | None = Field(default=None, max_length=80)
    plate_number: str | None = Field(default=None, max_length=20)
    colour: str | None = Field(default=None, max_length=40)
    parking_slot: str | None = Field(default=None, max_length=40)
    parking_tower: str | None = Field(default=None, max_length=80)

    @field_validator("nickname", "colour", "parking_slot", "parking_tower")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("plate_number")
    @classmethod
    def normalize_plate(cls, value: str | None) -> str | None:
        return normalize_indian_plate(value)


class VehiclePatch(BaseModel):
    """PATCH /me/vehicle — partial update (VEH-03). JSON null clears optional fields.

    Changing ``model_id`` re-derives ``size_tier`` from the catalog.
    """

    model_config = ConfigDict(extra="forbid")

    model_id: UUID | None = None
    nickname: str | None = Field(default=None, max_length=80)
    plate_number: str | None = Field(default=None, max_length=20)
    colour: str | None = Field(default=None, max_length=40)
    parking_slot: str | None = Field(default=None, max_length=40)
    parking_tower: str | None = Field(default=None, max_length=80)

    @field_validator("nickname", "colour", "parking_slot", "parking_tower")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("plate_number")
    @classmethod
    def normalize_plate(cls, value: str | None) -> str | None:
        return normalize_indian_plate(value)


class VehicleSizeTierOut(BaseModel):
    code: VehicleSizeTier
    label: str
    description: str


class VehicleSizeTierListOut(BaseModel):
    items: list[VehicleSizeTierOut]
