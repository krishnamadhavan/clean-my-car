"""App config / bootstrap schemas (Module 13)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AppConfigOut(BaseModel):
    min_ios_version: str
    force_update: bool
    feature_flags: dict[str, Any] = Field(default_factory=dict)
    support_whatsapp: str | None = None
    support_email: str | None = None
    support_phone: str | None = None
    support_whatsapp_url: str | None = None


class AppBootstrapOut(BaseModel):
    config: AppConfigOut
    authenticated: bool = False
    user_id: UUID | None = None
    has_vehicle: bool = False
    has_subscription: bool = False


class OpsAppConfigUpdateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_ios_version: str | None = Field(default=None, max_length=20)
    force_update: bool | None = None
    feature_flags: dict[str, Any] | None = None
    support_whatsapp: str | None = Field(default=None, max_length=40)
    support_email: str | None = Field(default=None, max_length=200)
    support_phone: str | None = Field(default=None, max_length=40)
    support_whatsapp_url: str | None = Field(default=None, max_length=500)
    notes: str | None = None
