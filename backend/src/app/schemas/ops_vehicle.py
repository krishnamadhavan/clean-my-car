"""Ops vehicle catalog schemas (Ops Module 5)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.plate import normalize_indian_plate
from app.models.vehicle import VehicleSizeTier


class OpsVehicleMakeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class OpsVehicleMakeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=120)
    is_active: bool = True
    # Omit or null → server assigns next free order (must stay unique).
    display_order: int | None = Field(default=None)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned


class OpsVehicleMakePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    is_active: bool | None = None
    display_order: int | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned


class OpsVehicleMakeListOut(BaseModel):
    items: list[OpsVehicleMakeOut]
    total: int
    page: int
    page_size: int


class OpsVehicleModelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    make_id: UUID
    name: str
    size_tier: VehicleSizeTier
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class OpsVehicleModelCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=120)
    size_tier: VehicleSizeTier
    is_active: bool = True
    display_order: int = 0

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned


class OpsVehicleModelPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    size_tier: VehicleSizeTier | None = None
    is_active: bool | None = None
    display_order: int | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name must not be empty")
        return cleaned


class OpsVehicleModelListOut(BaseModel):
    items: list[OpsVehicleModelOut]
    total: int
    page: int
    page_size: int


class OpsUserVehicleOut(BaseModel):
    """Consumer's registered vehicle (ops view)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    model_id: UUID
    size_tier: VehicleSizeTier
    nickname: str | None = None
    plate_number: str | None = None
    colour: str | None = None
    parking_slot: str | None = None
    parking_tower: str | None = None
    make: OpsVehicleMakeOut | None = None
    model: OpsVehicleModelOut | None = None
    created_at: datetime
    updated_at: datetime


class OpsUserVehiclePatch(BaseModel):
    """Correct user's vehicle (OPS-VEH-08). size_tier re-derived if model_id changes."""

    model_config = ConfigDict(extra="forbid")

    model_id: UUID | None = None
    nickname: str | None = Field(default=None, max_length=80)
    plate_number: str | None = Field(default=None, max_length=20)
    colour: str | None = Field(default=None, max_length=40)
    parking_slot: str | None = Field(default=None, max_length=40)
    parking_tower: str | None = Field(default=None, max_length=80)

    @field_validator("nickname", "colour", "parking_slot", "parking_tower")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("plate_number")
    @classmethod
    def validate_plate(cls, value: str | None) -> str | None:
        return normalize_indian_plate(value)
