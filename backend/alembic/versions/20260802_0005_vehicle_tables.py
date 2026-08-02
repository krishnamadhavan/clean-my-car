"""vehicle catalog (makes/models) and vehicles table

Revision ID: 20260802_0005
Revises: 20260802_0004
Create Date: 2026-08-02

Size tier is owned by vehicle_models (ops catalog). Users register a model_id;
vehicles.size_tier is a snapshot copied from the model at set/change time.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260802_0005"
down_revision: str | None = "20260802_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

vehicle_size_tier = postgresql.ENUM(
    "small",
    "medium",
    "large",
    name="vehicle_size_tier",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM(
        "small",
        "medium",
        "large",
        name="vehicle_size_tier",
    ).create(bind, checkfirst=True)

    # Drop any draft vehicles table from earlier WIP (no model_id).
    op.execute("DROP TABLE IF EXISTS vehicles CASCADE")

    op.create_table(
        "vehicle_makes",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
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
        sa.UniqueConstraint("name", name="uq_vehicle_makes_name"),
    )

    op.create_table(
        "vehicle_models",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("make_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("size_tier", vehicle_size_tier, nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
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
        sa.ForeignKeyConstraint(["make_id"], ["vehicle_makes.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_vehicle_models_make_id", "vehicle_models", ["make_id"])

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("model_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("size_tier", vehicle_size_tier, nullable=False),
        sa.Column("nickname", sa.String(length=80), nullable=True),
        sa.Column("plate_number", sa.String(length=20), nullable=True),
        sa.Column("colour", sa.String(length=40), nullable=True),
        sa.Column("parking_slot", sa.String(length=40), nullable=True),
        sa.Column("parking_tower", sa.String(length=80), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["model_id"], ["vehicle_models.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("user_id", name="uq_vehicles_user_id"),
    )
    op.create_index("ix_vehicles_user_id", "vehicles", ["user_id"], unique=True)
    op.create_index("ix_vehicles_model_id", "vehicles", ["model_id"])


def downgrade() -> None:
    op.drop_index("ix_vehicles_model_id", table_name="vehicles")
    op.drop_index("ix_vehicles_user_id", table_name="vehicles")
    op.drop_table("vehicles")

    op.drop_index("ix_vehicle_models_make_id", table_name="vehicle_models")
    op.drop_table("vehicle_models")
    op.drop_table("vehicle_makes")

    bind = op.get_bind()
    postgresql.ENUM(name="vehicle_size_tier").drop(bind, checkfirst=True)
