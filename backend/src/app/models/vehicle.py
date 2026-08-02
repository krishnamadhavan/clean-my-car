"""Vehicle catalog + single vehicle per user (Module 5).

Users pick make + model; size_tier is set from the catalog (ops-owned), never free choice.
"""

from __future__ import annotations

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class VehicleSizeTier(StrEnum):
    small = "small"
    medium = "medium"
    large = "large"


_size_tier_enum = Enum(
    VehicleSizeTier,
    name="vehicle_size_tier",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)


class VehicleMake(Base, TimestampMixin):
    """Brand / manufacturer (e.g. Maruti, Hyundai)."""

    __tablename__ = "vehicle_makes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    models: Mapped[list[VehicleModel]] = relationship(
        "VehicleModel",
        back_populates="make",
        cascade="all, delete-orphan",
    )


class VehicleModel(Base, TimestampMixin):
    """Specific model under a make; carries the ops-defined size tier."""

    __tablename__ = "vehicle_models"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    make_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("vehicle_makes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    size_tier: Mapped[VehicleSizeTier] = mapped_column(_size_tier_enum, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    make: Mapped[VehicleMake] = relationship("VehicleMake", back_populates="models")
    vehicles: Mapped[list[Vehicle]] = relationship("Vehicle", back_populates="model")


class Vehicle(Base, TimestampMixin):
    """User's single registered car (v1: one per account)."""

    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    model_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("vehicle_models.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Snapshot of catalog tier at set/change time (pricing stability if ops reclassifies later)
    size_tier: Mapped[VehicleSizeTier] = mapped_column(_size_tier_enum, nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(80), nullable=True)
    plate_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    colour: Mapped[str | None] = mapped_column(String(40), nullable=True)
    parking_slot: Mapped[str | None] = mapped_column(String(40), nullable=True)
    parking_tower: Mapped[str | None] = mapped_column(String(80), nullable=True)

    user: Mapped[User] = relationship("User", foreign_keys=[user_id], back_populates="vehicle")
    model: Mapped[VehicleModel] = relationship("VehicleModel", back_populates="vehicles")
