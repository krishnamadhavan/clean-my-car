"""ops_operators and ops_refresh_tokens (Ops Module 1)

Revision ID: 20260803_0007
Revises: 20260802_0006
Create Date: 2026-08-03

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260803_0007"
down_revision: str | None = "20260802_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ops_operators",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "roles",
            postgresql.ARRAY(sa.String(length=64)),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.UniqueConstraint("email", name="uq_ops_operators_email"),
    )
    op.create_index("ix_ops_operators_email", "ops_operators", ["email"], unique=True)

    op.create_table(
        "ops_refresh_tokens",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("operator_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["operator_id"], ["ops_operators.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token_hash", name="uq_ops_refresh_tokens_token_hash"),
    )
    op.create_index("ix_ops_refresh_tokens_operator_id", "ops_refresh_tokens", ["operator_id"])
    op.create_index("ix_ops_refresh_tokens_token_hash", "ops_refresh_tokens", ["token_hash"])


def downgrade() -> None:
    op.drop_index("ix_ops_refresh_tokens_token_hash", table_name="ops_refresh_tokens")
    op.drop_index("ix_ops_refresh_tokens_operator_id", table_name="ops_refresh_tokens")
    op.drop_table("ops_refresh_tokens")
    op.drop_index("ix_ops_operators_email", table_name="ops_operators")
    op.drop_table("ops_operators")
