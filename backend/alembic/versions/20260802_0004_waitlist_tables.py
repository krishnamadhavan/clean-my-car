"""waitlist_entries table (Module 4)

Revision ID: 20260802_0004
Revises: 20260801_0003
Create Date: 2026-08-02

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260802_0004"
down_revision: str | None = "20260801_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

waitlist_status = postgresql.ENUM(
    "pending",
    "contacted",
    "converted",
    "closed",
    name="waitlist_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    postgresql.ENUM(
        "pending",
        "contacted",
        "converted",
        "closed",
        name="waitlist_status",
    ).create(bind, checkfirst=True)

    op.create_table(
        "waitlist_entries",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("city_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("society_name", sa.String(length=200), nullable=False),
        sa.Column("phone", sa.String(length=16), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "status",
            waitlist_status,
            server_default="pending",
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"], ondelete="CASCADE"),
    )
    # Unique when set: one waitlist entry per authenticated user (Postgres allows
    # multiple NULLs under a UNIQUE constraint for anonymous joins).
    op.create_index("ix_waitlist_entries_user_id", "waitlist_entries", ["user_id"], unique=True)
    op.create_index("ix_waitlist_entries_city_id", "waitlist_entries", ["city_id"])
    op.create_index("ix_waitlist_entries_phone", "waitlist_entries", ["phone"])


def downgrade() -> None:
    op.drop_index("ix_waitlist_entries_phone", table_name="waitlist_entries")
    op.drop_index("ix_waitlist_entries_city_id", table_name="waitlist_entries")
    op.drop_index("ix_waitlist_entries_user_id", table_name="waitlist_entries")
    op.drop_table("waitlist_entries")

    bind = op.get_bind()
    postgresql.ENUM(name="waitlist_status").drop(bind, checkfirst=True)
