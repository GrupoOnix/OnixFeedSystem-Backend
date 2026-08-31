"""add sensor measurement metadata

Revision ID: d9e1f0a2b3c4
Revises: c7f4e2a91b63
Create Date: 2026-08-31 01:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d9e1f0a2b3c4"
down_revision: Union[str, None] = "c7f4e2a91b63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sensors", sa.Column("measurement_unit", sa.String(length=30), nullable=True))
    op.add_column("sensors", sa.Column("calibration_value", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("sensors", "calibration_value")
    op.drop_column("sensors", "measurement_unit")
