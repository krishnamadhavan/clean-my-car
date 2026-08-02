"""City-specific pricing catalog (Module 6).

Amounts are stored in **paise** (INR minor units). Base monthly price is by
vehicle size; interior is an add-on by frequency (0 / 1 / 2 / 4 per month).
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin
from app.models.vehicle import VehicleSizeTier

_size_tier_enum = Enum(
    VehicleSizeTier,
    name="vehicle_size_tier",
    create_type=False,
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)

if TYPE_CHECKING:
    from app.models.city import City


class CityPricing(Base, TimestampMixin):
    """Per-city pricing presentation settings (GST flags, currency)."""

    __tablename__ = "city_pricing"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="INR", server_default="INR"
    )
    # When true, listed amounts already include GST; when false, GST is added on top.
    amounts_include_gst: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    # GST rate in basis points (1800 = 18%). Used for tax breakdown presentation.
    gst_rate_bps: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1800, server_default="1800"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    city: Mapped[City] = relationship("City", foreign_keys=[city_id])
    size_prices: Mapped[list[CitySizePrice]] = relationship(
        "CitySizePrice",
        back_populates="pricing",
        cascade="all, delete-orphan",
    )
    interior_prices: Mapped[list[CityInteriorPrice]] = relationship(
        "CityInteriorPrice",
        back_populates="pricing",
        cascade="all, delete-orphan",
    )


class CitySizePrice(Base, TimestampMixin):
    """Base monthly exterior price for a size tier in a city (paise)."""

    __tablename__ = "city_size_prices"
    __table_args__ = (
        UniqueConstraint("pricing_id", "size_tier", name="uq_city_size_prices_pricing_size"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pricing_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("city_pricing.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    size_tier: Mapped[VehicleSizeTier] = mapped_column(_size_tier_enum, nullable=False)
    monthly_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)

    pricing: Mapped[CityPricing] = relationship("CityPricing", back_populates="size_prices")


class CityInteriorPrice(Base, TimestampMixin):
    """Interior add-on monthly price by frequency for a city (paise).

    ``interior_frequency`` is cleans per calendar month: 0, 1, 2, or 4.
    Frequency 0 is usually amount 0 and may be omitted.
    """

    __tablename__ = "city_interior_prices"
    __table_args__ = (
        UniqueConstraint(
            "pricing_id",
            "interior_frequency",
            name="uq_city_interior_prices_pricing_freq",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pricing_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("city_pricing.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interior_frequency: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_amount_paise: Mapped[int] = mapped_column(Integer, nullable=False)

    pricing: Mapped[CityPricing] = relationship("CityPricing", back_populates="interior_prices")
