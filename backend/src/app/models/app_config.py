"""App remote config singleton (Module 13)."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin


class AppConfig(Base, TimestampMixin):
    """Single-row app config (id is fixed usage; latest active row wins)."""

    __tablename__ = "app_config"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    min_ios_version: Mapped[str] = mapped_column(String(20), nullable=False, default="17.0")
    force_update: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    feature_flags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    support_whatsapp: Mapped[str | None] = mapped_column(String(40), nullable=True)
    support_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    support_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    support_whatsapp_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
