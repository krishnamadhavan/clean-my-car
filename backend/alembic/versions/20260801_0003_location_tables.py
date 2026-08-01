"""cities, societies, user location FKs

Revision ID: 20260801_0003
Revises: 20260801_0002
Create Date: 2026-08-01

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260801_0003"
down_revision: str | None = "20260801_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cities",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("state", sa.String(length=120), nullable=False),
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
    )

    op.create_table(
        "societies",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("city_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("address_line", sa.String(length=255), nullable=True),
        sa.Column("service_weekdays", postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column("is_serviceable", sa.Boolean(), server_default="true", nullable=False),
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
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_societies_city_id", "societies", ["city_id"])
    op.create_index("ix_societies_name", "societies", ["name"])

    op.add_column("users", sa.Column("city_id", sa.Uuid(as_uuid=True), nullable=True))
    op.add_column("users", sa.Column("society_id", sa.Uuid(as_uuid=True), nullable=True))
    op.create_index("ix_users_city_id", "users", ["city_id"])
    op.create_index("ix_users_society_id", "users", ["society_id"])
    op.create_foreign_key(
        "fk_users_city_id_cities",
        "users",
        "cities",
        ["city_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_users_society_id_societies",
        "users",
        "societies",
        ["society_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_users_society_id_societies", "users", type_="foreignkey")
    op.drop_constraint("fk_users_city_id_cities", "users", type_="foreignkey")
    op.drop_index("ix_users_society_id", table_name="users")
    op.drop_index("ix_users_city_id", table_name="users")
    op.drop_column("users", "society_id")
    op.drop_column("users", "city_id")

    op.drop_index("ix_societies_name", table_name="societies")
    op.drop_index("ix_societies_city_id", table_name="societies")
    op.drop_table("societies")
    op.drop_table("cities")
