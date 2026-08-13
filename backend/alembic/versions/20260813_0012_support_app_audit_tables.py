"""content, support tickets, app config, audit (modules 12–15)

Revision ID: 20260813_0012
Revises: 20260813_0011
Create Date: 2026-08-13

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260813_0012"
down_revision: str | None = "20260813_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

legal_doc_type = postgresql.ENUM(
    "terms",
    "privacy",
    "cancellation",
    name="legal_doc_type",
    create_type=False,
)
support_ticket_status = postgresql.ENUM(
    "open",
    "in_progress",
    "resolved",
    "closed",
    name="support_ticket_status",
    create_type=False,
)
support_ticket_category = postgresql.ENUM(
    "billing",
    "service",
    "account",
    "other",
    name="support_ticket_category",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    legal_doc_type.create(bind, checkfirst=True)
    support_ticket_status.create(bind, checkfirst=True)
    support_ticket_category.create(bind, checkfirst=True)

    op.create_table(
        "faq_entries",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("question", sa.String(length=500), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False, server_default="general"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
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
        "legal_documents",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("doc_type", legal_doc_type, nullable=False),
        sa.Column("version", sa.String(length=40), nullable=False, server_default="1.0"),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index("ix_legal_documents_doc_type", "legal_documents", ["doc_type"])

    op.create_table(
        "support_tickets",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "category",
            support_ticket_category,
            nullable=False,
            server_default="other",
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "status",
            support_ticket_status,
            nullable=False,
            server_default="open",
        ),
        sa.Column(
            "wash_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("washes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "payment_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("payments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("ops_notes", sa.Text(), nullable=True),
        sa.Column("ops_reply", sa.Text(), nullable=True),
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
    op.create_index("ix_support_tickets_user_id", "support_tickets", ["user_id"])
    op.create_index("ix_support_tickets_status", "support_tickets", ["status"])

    op.create_table(
        "app_config",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("min_ios_version", sa.String(length=20), nullable=False, server_default="17.0"),
        sa.Column("force_update", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "feature_flags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("support_whatsapp", sa.String(length=40), nullable=True),
        sa.Column("support_email", sa.String(length=200), nullable=True),
        sa.Column("support_phone", sa.String(length=40), nullable=True),
        sa.Column("support_whatsapp_url", sa.String(length=500), nullable=True),
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

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "operator_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("ops_operators.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.String(length=80), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
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
    op.create_index("ix_audit_events_operator_id", "audit_events", ["operator_id"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_resource_type", "audit_events", ["resource_type"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_resource_type", table_name="audit_events")
    op.drop_index("ix_audit_events_action", table_name="audit_events")
    op.drop_index("ix_audit_events_operator_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_table("app_config")
    op.drop_index("ix_support_tickets_status", table_name="support_tickets")
    op.drop_index("ix_support_tickets_user_id", table_name="support_tickets")
    op.drop_table("support_tickets")
    op.drop_index("ix_legal_documents_doc_type", table_name="legal_documents")
    op.drop_table("legal_documents")
    op.drop_table("faq_entries")
    support_ticket_category.drop(op.get_bind(), checkfirst=True)
    support_ticket_status.drop(op.get_bind(), checkfirst=True)
    legal_doc_type.drop(op.get_bind(), checkfirst=True)
