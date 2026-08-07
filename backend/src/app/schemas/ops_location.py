"""Ops location / catalog schemas (Ops Module 3)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OpsCityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    state: str
    is_active: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class OpsCityCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=120)
    state: str = Field(..., min_length=1, max_length=120)
    is_active: bool = True
    # Omit or null → server assigns next free order (must stay unique).
    display_order: int | None = Field(default=None)

    @field_validator("name", "state")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned


class OpsCityPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    state: str | None = Field(default=None, min_length=1, max_length=120)
    is_active: bool | None = None
    display_order: int | None = None

    @field_validator("name", "state")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned


class OpsCityListOut(BaseModel):
    items: list[OpsCityOut]
    total: int
    page: int
    page_size: int


class OpsSocietyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    city_id: UUID
    name: str
    address_line: str | None = None
    service_weekdays: list[int]
    is_serviceable: bool
    display_order: int
    created_at: datetime
    updated_at: datetime


class OpsSocietyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200)
    address_line: str | None = Field(default=None, max_length=255)
    service_weekdays: list[int] = Field(..., min_length=3, max_length=3)
    is_serviceable: bool = True
    display_order: int = 0

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("address_line")
    @classmethod
    def strip_address(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("service_weekdays")
    @classmethod
    def validate_weekdays(cls, value: list[int]) -> list[int]:
        if len(value) != 3:
            raise ValueError("exactly 3 service weekdays required")
        if len(set(value)) != 3:
            raise ValueError("service weekdays must be unique")
        for d in value:
            # 0=Mon … 5=Sat; Sunday (6) is not a service day.
            if d < 0 or d > 5:
                raise ValueError("weekdays must be 0 (Mon) … 5 (Sat); Sunday is not allowed")
        return sorted(value)


class OpsSocietyPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=200)
    address_line: str | None = Field(default=None, max_length=255)
    service_weekdays: list[int] | None = Field(default=None, min_length=3, max_length=3)
    is_serviceable: bool | None = None
    display_order: int | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("address_line")
    @classmethod
    def strip_address(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("service_weekdays")
    @classmethod
    def validate_weekdays(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        if len(value) != 3:
            raise ValueError("exactly 3 service weekdays required")
        if len(set(value)) != 3:
            raise ValueError("service weekdays must be unique")
        for d in value:
            if d < 0 or d > 5:
                raise ValueError("weekdays must be 0 (Mon) … 5 (Sat); Sunday is not allowed")
        return sorted(value)


class OpsSocietyListOut(BaseModel):
    items: list[OpsSocietyOut]
    total: int
    page: int
    page_size: int
