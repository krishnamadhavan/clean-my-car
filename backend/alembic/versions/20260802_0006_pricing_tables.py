"""city pricing tables (Module 6)

Revision ID: 20260802_0006
Revises: 20260802_0005
Create Date: 2026-08-02

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260802_0006"
down_revision: str | None = "20260802_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Reuse existing vehicle_size_tier enum created in 0005
vehicle_size_tier = postgresql.ENUM(
    "small",
    "medium",
    "large",
    name="vehicle_size_tier",
    create_type=False,
)


def upgrade() -> None:
    op.create_table(
        "city_pricing",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("city_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("amounts_include_gst", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("gst_rate_bps", sa.Integer(), server_default="1800", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("city_id", name="uq_city_pricing_city_id"),
    )
    op.create_index("ix_city_pricing_city_id", "city_pricing", ["city_id"], unique=True)

    op.create_table(
        "city_size_prices",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("pricing_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("size_tier", vehicle_size_tier, nullable=False),
        sa.Column("monthly_amount_paise", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["pricing_id"], ["city_pricing.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("pricing_id", "size_tier", name="uq_city_size_prices_pricing_size"),
    )
    op.create_index("ix_city_size_prices_pricing_id", "city_size_prices", ["pricing_id"])

    op.create_table(
        "city_interior_prices",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("pricing_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("interior_frequency", sa.Integer(), nullable=False),
        sa.Column("monthly_amount_paise", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["pricing_id"], ["city_pricing.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "pricing_id",
            "interior_frequency",
            name="uq_city_interior_prices_pricing_freq",
        ),
    )
    op.create_index("ix_city_interior_prices_pricing_id", "city_interior_prices", ["pricing_id"])


def downgrade() -> None:
    op.drop_index("ix_city_interior_prices_pricing_id", table_name="city_interior_prices")
    op.drop_table("city_interior_prices")
    op.drop_index("ix_city_size_prices_pricing_id", table_name="city_size_prices")
    op.drop_table("city_size_prices")
    op.drop_index("ix_city_pricing_city_id", table_name="city_pricing")
    op.drop_table("city_pricing")
