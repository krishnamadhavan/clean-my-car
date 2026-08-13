"""Notification preferences and ops templates (Module 11)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class NotificationPreferences(Base, TimestampMixin):
    """Per-user notification toggles (one row per user)."""

    __tablename__ = "notification_preferences"
    __table_args__ = (UniqueConstraint("user_id", name="uq_notification_preferences_user"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    wash_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    payment_events: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    service_reminders: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    marketing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped[User] = relationship("User", foreign_keys=[user_id])


class NotificationTemplate(Base, TimestampMixin):
    """Ops-editable copy templates (keyed)."""

    __tablename__ = "notification_templates"
    __table_args__ = (UniqueConstraint("key", name="uq_notification_templates_key"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(40), nullable=False, default="push")
