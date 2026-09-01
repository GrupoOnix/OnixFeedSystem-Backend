"""allow multiple scheduled plans per feeding line

Revision ID: e5f6a7b8c9d0
Revises: b4c7d8e9f0a1
Create Date: 2026-08-31 03:00:00
"""

from typing import Sequence, Union

from alembic import op


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "b4c7d8e9f0a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_scheduled_feeding_plans_line_id",
        "scheduled_feeding_plans",
        type_="unique",
    )


def downgrade() -> None:
    op.create_unique_constraint(
        "uq_scheduled_feeding_plans_line_id",
        "scheduled_feeding_plans",
        ["line_id"],
    )
