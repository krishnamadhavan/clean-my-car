"""Consumer schedule schemas (WASH-04)."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class ScheduleOccurrenceKind(StrEnum):
    scheduled = "scheduled"
    retry_scheduled = "retry_scheduled"


class ScheduleOccurrenceOut(BaseModel):
    """One upcoming wash day (service day or retry)."""

    date: date
    weekday: int = Field(description="0=Monday … 6=Sunday")
    weekday_label: str
    kind: ScheduleOccurrenceKind
    title: str
    note: str | None = None
    society_id: UUID | None = None
    society_name: str | None = None


class ScheduleOut(BaseModel):
    """GET /me/schedule — only days with a planned wash."""

    items: list[ScheduleOccurrenceOut]
    service_weekdays: list[int] = Field(default_factory=list)
    service_weekday_labels: list[str] = Field(default_factory=list)
    subscription_id: UUID | None = None
    subscription_status: str | None = None
    from_date: date
    until_date: date
    message: str | None = None
