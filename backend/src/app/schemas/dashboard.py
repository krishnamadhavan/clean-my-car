"""Consumer dashboard aggregate (DASH-01)."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.location import CityOut, SocietySummaryOut
from app.schemas.subscription import SubscriptionOut
from app.schemas.vehicle import VehicleOut
from app.schemas.wash import WashSummaryOut


class DashboardNextServiceOut(BaseModel):
    date: date
    kind: str
    title: str
    is_retry: bool = False
    wash_id: UUID | None = None


class DashboardOut(BaseModel):
    """GET /me/dashboard — home hero data."""

    has_subscription: bool
    subscription: SubscriptionOut | None = None
    vehicle: VehicleOut | None = None
    city: CityOut | None = None
    society: SocietySummaryOut | None = None
    service_weekdays: list[int] = Field(default_factory=list)
    service_weekday_labels: list[str] = Field(default_factory=list)
    wash_summary: WashSummaryOut | None = None
    next_service: DashboardNextServiceOut | None = None
    amount_due_paise: int = 0
    currency: str = "INR"
    billing_message: str | None = None
    message: str | None = None
