"""washes, devices, notification prefs/templates (modules 9–11)

Revision ID: 20260813_0011
Revises: 20260812_0010
Create Date: 2026-08-13

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260813_0011"
down_revision: str | None = "20260812_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

wash_status = postgresql.ENUM(
    "scheduled",
    "completed",
    "missed",
    "retry_scheduled",
    "skipped",
    name="wash_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    wash_status.create(bind, checkfirst=True)

    op.create_table(
        "washes",
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
            sa.ForeignKey("subscriptions.id", ondelete="CASCADE"),
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
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            wash_status,
            nullable=False,
            server_default="scheduled",
        ),
        sa.Column("includes_exterior", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("includes_interior", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "completed_by_operator_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("ops_operators.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("miss_reason", sa.String(length=500), nullable=True),
        sa.Column(
            "retry_of_wash_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("washes.id", ondelete="SET NULL"),
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
        sa.UniqueConstraint("user_id", "service_date", name="uq_washes_user_service_date"),
    )
    op.create_index("ix_washes_user_id", "washes", ["user_id"])
    op.create_index("ix_washes_subscription_id", "washes", ["subscription_id"])
    op.create_index("ix_washes_society_id", "washes", ["society_id"])
    op.create_index("ix_washes_service_date", "washes", ["service_date"])
    op.create_index("ix_washes_status", "washes", ["status"])

    op.create_table(
        "user_devices",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.String(length=512), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=False, server_default="ios"),
        sa.Column("app_version", sa.String(length=40), nullable=True),
        sa.Column("device_name", sa.String(length=120), nullable=True),
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
        sa.UniqueConstraint("token", name="uq_user_devices_token"),
    )
    op.create_index("ix_user_devices_user_id", "user_devices", ["user_id"])

    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("wash_completed", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("payment_events", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("service_reminders", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("marketing", sa.Boolean(), nullable=False, server_default=sa.false()),
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
        sa.UniqueConstraint("user_id", name="uq_notification_preferences_user"),
    )
    op.create_index("ix_notification_preferences_user_id", "notification_preferences", ["user_id"])

    op.create_table(
        "notification_templates",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("channel", sa.String(length=40), nullable=False, server_default="push"),
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
        sa.UniqueConstraint("key", name="uq_notification_templates_key"),
    )


def downgrade() -> None:
    op.drop_table("notification_templates")
    op.drop_index("ix_notification_preferences_user_id", table_name="notification_preferences")
    op.drop_table("notification_preferences")
    op.drop_index("ix_user_devices_user_id", table_name="user_devices")
    op.drop_table("user_devices")
    op.drop_index("ix_washes_status", table_name="washes")
    op.drop_index("ix_washes_service_date", table_name="washes")
    op.drop_index("ix_washes_society_id", table_name="washes")
    op.drop_index("ix_washes_subscription_id", table_name="washes")
    op.drop_index("ix_washes_user_id", table_name="washes")
    op.drop_table("washes")
    wash_status.drop(op.get_bind(), checkfirst=True)
