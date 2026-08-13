"""Ops notification template schemas (OPS-NOTIF-*)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OpsNotificationTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    key: str
    title: str
    body: str
    channel: str
    created_at: datetime
    updated_at: datetime


class OpsNotificationTemplateListOut(BaseModel):
    items: list[OpsNotificationTemplateOut]


class OpsNotificationTemplateUpsertIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1)
    channel: str = Field(default="push", max_length=40)


class OpsNotificationSendIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: UUID | None = None
    template_key: str | None = Field(default=None, max_length=80)
    title: str | None = Field(default=None, max_length=200)
    body: str | None = None


class OpsNotificationSendOut(BaseModel):
    accepted: bool
    message: str
