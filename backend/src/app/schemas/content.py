"""Content / FAQ / legal / contact schemas (Module 12)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.content import LegalDocType


class FaqEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    question: str
    answer: str
    category: str
    display_order: int


class FaqListOut(BaseModel):
    items: list[FaqEntryOut]


class LegalDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doc_type: LegalDocType
    version: str
    title: str
    body: str | None = None
    url: str | None = None
    published_at: datetime | None = None


class ContactChannelsOut(BaseModel):
    whatsapp: str | None = None
    whatsapp_url: str | None = None
    email: str | None = None
    phone: str | None = None
    message: str | None = None


class OpsFaqEntryIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=500)
    answer: str = Field(min_length=1)
    category: str = Field(default="general", max_length=80)
    display_order: int = 0
    is_active: bool = True


class OpsFaqReplaceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[OpsFaqEntryIn]


class OpsLegalDocumentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = Field(default="1.0", max_length=40)
    title: str = Field(min_length=1, max_length=200)
    body: str | None = None
    url: str | None = Field(default=None, max_length=500)
    is_active: bool = True
