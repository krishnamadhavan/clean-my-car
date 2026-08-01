"""Location / eligibility schemas (Module 3)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# 0=Monday … 6=Sunday
WEEKDAY_LABELS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


class CityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    state: str
    display_order: int


class SocietySummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    city_id: UUID
    name: str
    address_line: str | None = None
    service_weekdays: list[int]
    service_weekday_labels: list[str] = Field(default_factory=list)
    display_order: int

    @classmethod
    def from_society(cls, society: object) -> SocietySummaryOut:
        weekdays: list[int] = list(society.service_weekdays or [])
        labels = [WEEKDAY_LABELS[d] for d in weekdays if 0 <= d <= 6]
        return cls(
            id=society.id,
            city_id=society.city_id,
            name=society.name,
            address_line=society.address_line,
            service_weekdays=weekdays,
            service_weekday_labels=labels,
            display_order=society.display_order,
        )


class SocietyDetailOut(SocietySummaryOut):
    city: CityOut
    is_serviceable: bool = True


class SocietyListOut(BaseModel):
    items: list[SocietySummaryOut]
    total: int
    page: int
    page_size: int


class UserLocationOut(BaseModel):
    city: CityOut | None = None
    society: SocietySummaryOut | None = None
    updated_at: datetime | None = None


class UserLocationUpdate(BaseModel):
    city_id: UUID
    society_id: UUID
