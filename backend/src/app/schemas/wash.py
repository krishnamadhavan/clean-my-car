"""Consumer wash schemas (Module 10)."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.wash import WashStatus


class WashOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subscription_id: UUID
    society_id: UUID
    vehicle_id: UUID | None = None
    service_date: date
    status: WashStatus
    includes_exterior: bool
    includes_interior: bool
    completed_at: datetime | None = None
    miss_reason: str | None = None
    retry_of_wash_id: UUID | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class WashListOut(BaseModel):
    items: list[WashOut]
    total: int
    page: int
    page_size: int


class WashSummaryOut(BaseModel):
    """GET /me/washes/summary — current calendar month."""

    year_month: str
    exterior_entitled: int
    exterior_completed: int
    exterior_pending: int
    exterior_missed: int
    interior_included: int
    interior_completed: int
    subscription_id: UUID | None = None
    subscription_status: str | None = None
    message: str | None = None
