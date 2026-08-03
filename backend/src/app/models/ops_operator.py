"""Ops operator accounts (email/password — not consumer phone OTP)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, Uuid
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.ops_refresh_token import OpsRefreshToken

# Well-known role strings (enforced in app logic; stored as free-form strings for flexibility)
OPS_ROLE_CATALOG_ADMIN = "catalog_admin"
OPS_ROLE_FIELD_OPS = "field_ops"
OPS_ROLE_SUPPORT = "support"
KNOWN_OPS_ROLES = frozenset({OPS_ROLE_CATALOG_ADMIN, OPS_ROLE_FIELD_OPS, OPS_ROLE_SUPPORT})


class OpsOperator(Base, TimestampMixin):
    __tablename__ = "ops_operators"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    roles: Mapped[list[str]] = mapped_column(
        ARRAY(String(64)),
        nullable=False,
        default=list,
        server_default="{}",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    refresh_tokens: Mapped[list[OpsRefreshToken]] = relationship(
        "OpsRefreshToken",
        back_populates="operator",
        cascade="all, delete-orphan",
    )
