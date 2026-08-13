"""Consumer notification schemas (Module 11)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DeviceUpsertIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=8, max_length=512)
    platform: str = Field(default="ios", max_length=20)
    app_version: str | None = Field(default=None, max_length=40)
    device_name: str | None = Field(default=None, max_length=120)


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    token: str
    platform: str
    app_version: str | None = None
    device_name: str | None = None
    created_at: datetime
    updated_at: datetime


class NotificationPreferencesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    wash_completed: bool
    payment_events: bool
    service_reminders: bool
    marketing: bool
    updated_at: datetime | None = None


class NotificationPreferencesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    wash_completed: bool | None = None
    payment_events: bool | None = None
    service_reminders: bool | None = None
    marketing: bool | None = None
