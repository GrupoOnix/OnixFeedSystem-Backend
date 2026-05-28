"""add cyclic wait after visit

Revision ID: d4e5f6a7b8c9
Revises: c2d3e4f5a6b7
Create Date: 2026-05-28 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "last_valid_cyclic_feeding_configs",
        sa.Column(
            "wait_after_visit_seconds",
            sa.Float(),
            server_default="0",
            nullable=False,
        ),
    )
    op.alter_column(
        "last_valid_cyclic_feeding_configs",
        "wait_after_visit_seconds",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column(
        "last_valid_cyclic_feeding_configs",
        "wait_after_visit_seconds",
    )
