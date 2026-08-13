"""subscriptions and payments tables (modules 7–8)

Revision ID: 20260812_0010
Revises: 20260807_0009
Create Date: 2026-08-12

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260812_0010"
down_revision: str | None = "20260807_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

subscription_status = postgresql.ENUM(
    "pending_payment",
    "active",
    "cancel_scheduled",
    "paused",
    "expired",
    "inactive",
    name="subscription_status",
    create_type=False,
)
payment_status = postgresql.ENUM(
    "pending",
    "succeeded",
    "failed",
    "cancelled",
    name="payment_status",
    create_type=False,
)
payment_kind = postgresql.ENUM(
    "subscription_start",
    "renewal",
    "adjustment",
    name="payment_kind",
    create_type=False,
)
# Reuse existing vehicle_size_tier enum from migration 0005
vehicle_size_tier = postgresql.ENUM(
    "small",
    "medium",
    "large",
    name="vehicle_size_tier",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    subscription_status.create(bind, checkfirst=True)
    payment_status.create(bind, checkfirst=True)
    payment_kind.create(bind, checkfirst=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "city_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("cities.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "society_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("societies.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "vehicle_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("vehicles.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("size_tier", vehicle_size_tier, nullable=False),
        sa.Column("interior_frequency", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", subscription_status, nullable=False),
        sa.Column("monthly_amount_paise", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("cancel_at", sa.Date(), nullable=True),
        sa.Column("paused_from", sa.Date(), nullable=True),
        sa.Column("paused_until", sa.Date(), nullable=True),
        sa.Column("notes", sa.String(length=1000), nullable=True),
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
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_city_id", "subscriptions", ["city_id"])
    op.create_index("ix_subscriptions_society_id", "subscriptions", ["society_id"])
    op.create_index("ix_subscriptions_vehicle_id", "subscriptions", ["vehicle_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subscription_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("subscriptions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("amount_paise", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("status", payment_status, nullable=False),
        sa.Column("kind", payment_kind, nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="manual"),
        sa.Column("provider_ref", sa.String(length=120), nullable=True),
        sa.Column("failure_reason", sa.String(length=500), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "reconciled_by_operator_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("ops_operators.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
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
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_index("ix_payments_subscription_id", "payments", ["subscription_id"])
    op.create_index("ix_payments_status", "payments", ["status"])


def downgrade() -> None:
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_payments_subscription_id", table_name="payments")
    op.drop_index("ix_payments_user_id", table_name="payments")
    op.drop_table("payments")

    op.drop_index("ix_subscriptions_status", table_name="subscriptions")
    op.drop_index("ix_subscriptions_vehicle_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_society_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_city_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")

    bind = op.get_bind()
    payment_kind.drop(bind, checkfirst=True)
    payment_status.drop(bind, checkfirst=True)
    subscription_status.drop(bind, checkfirst=True)
