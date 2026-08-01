"""User response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phone: str
    name: str | None = None
    email: str | None = None
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    """Used later by profile module; kept here for shared typing."""

    name: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=255)
