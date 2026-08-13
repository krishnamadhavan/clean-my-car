"""Support ticket schemas (Module 12)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.support import SupportTicketCategory, SupportTicketStatus


class SupportTicketCreateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: SupportTicketCategory = SupportTicketCategory.other
    message: str = Field(min_length=1, max_length=5000)
    wash_id: UUID | None = None
    payment_id: UUID | None = None


class SupportTicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: SupportTicketCategory
    message: str
    status: SupportTicketStatus
    wash_id: UUID | None = None
    payment_id: UUID | None = None
    ops_reply: str | None = None
    created_at: datetime
    updated_at: datetime


class SupportTicketListOut(BaseModel):
    items: list[SupportTicketOut]
    total: int
    page: int
    page_size: int


class OpsSupportTicketOut(SupportTicketOut):
    user_id: UUID
    user_phone: str | None = None
    user_name: str | None = None
    ops_notes: str | None = None


class OpsSupportTicketListOut(BaseModel):
    items: list[OpsSupportTicketOut]
    total: int
    page: int
    page_size: int


class OpsSupportTicketPatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: SupportTicketStatus | None = None
    ops_notes: str | None = Field(default=None, max_length=5000)
    ops_reply: str | None = Field(default=None, max_length=5000)
