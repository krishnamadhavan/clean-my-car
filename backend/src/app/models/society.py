"""Apartment society (only serviceable/live rows are listed for consumers)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.city import City


class Society(Base, TimestampMixin):
    __tablename__ = "societies"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cities.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    address_line: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Weekday numbers: 0=Monday … 5=Saturday (Sunday not serviceable). Exactly 3 for v1.
    service_weekdays: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    is_serviceable: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    city: Mapped[City] = relationship("City", back_populates="societies")
