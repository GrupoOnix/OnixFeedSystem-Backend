"""make pulse calibration target optional

Revision ID: b4c7d8e9f0a1
Revises: d9e1f0a2b3c4
Create Date: 2026-08-31 02:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "b4c7d8e9f0a1"
down_revision: Union[str, None] = "d9e1f0a2b3c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "doser_calibration_sessions",
        "target_grams",
        existing_type=sa.Float(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "doser_calibration_sessions",
        "target_grams",
        existing_type=sa.Float(),
        nullable=False,
    )
