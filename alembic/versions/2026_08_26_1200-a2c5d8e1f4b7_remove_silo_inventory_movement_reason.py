"""remove silo inventory movement reason

Revision ID: a2c5d8e1f4b7
Revises: 9c1e7a4b2d10
Create Date: 2026-08-26 12:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a2c5d8e1f4b7"
down_revision: Union[str, None] = "9c1e7a4b2d10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("silo_inventory_movements", "reason")


def downgrade() -> None:
    op.add_column("silo_inventory_movements", sa.Column("reason", sa.Text(), nullable=True))
