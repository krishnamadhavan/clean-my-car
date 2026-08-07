"""vehicle_makes.display_order unique

Revision ID: 20260807_0009
Revises: 20260807_0008
Create Date: 2026-08-07

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260807_0009"
down_revision: str | None = "20260807_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Deduplicate existing rows before adding the unique constraint.
    op.execute(
        sa.text(
            """
            WITH ordered AS (
                SELECT
                    id,
                    (ROW_NUMBER() OVER (
                        ORDER BY display_order ASC, name ASC, id ASC
                    ) - 1) AS new_order
                FROM vehicle_makes
            )
            UPDATE vehicle_makes AS m
            SET display_order = ordered.new_order
            FROM ordered
            WHERE m.id = ordered.id
            """
        )
    )
    op.create_index(
        "uq_vehicle_makes_display_order",
        "vehicle_makes",
        ["display_order"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_vehicle_makes_display_order", table_name="vehicle_makes")
