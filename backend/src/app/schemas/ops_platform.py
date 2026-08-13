"""Ops platform schemas (Module 15)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    operator_id: UUID | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    details: dict[str, Any] | None = None
    summary: str | None = None
    created_at: datetime


class AuditEventListOut(BaseModel):
    items: list[AuditEventOut]
    total: int
    page: int
    page_size: int


class SeedPreviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cities: list[dict[str, Any]] = Field(default_factory=list)
    societies: list[dict[str, Any]] = Field(default_factory=list)
    vehicle_makes: list[dict[str, Any]] = Field(default_factory=list)
    vehicle_models: list[dict[str, Any]] = Field(default_factory=list)
    pricing: list[dict[str, Any]] = Field(default_factory=list)


class SeedPreviewOut(BaseModel):
    dry_run: bool = True
    would_create_cities: int = 0
    would_create_societies: int = 0
    would_create_makes: int = 0
    would_create_models: int = 0
    would_create_pricing: int = 0
    warnings: list[str] = Field(default_factory=list)
    message: str
