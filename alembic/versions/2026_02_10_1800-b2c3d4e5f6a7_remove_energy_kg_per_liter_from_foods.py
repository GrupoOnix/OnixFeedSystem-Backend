"""remove_energy_kg_per_liter_from_foods

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-10 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("foods", "energy")
    op.drop_column("foods", "kg_per_liter")


def downgrade() -> None:
    op.add_column(
        "foods",
        sa.Column("kg_per_liter", sa.Float(), nullable=False, server_default="0.5"),
    )
    op.add_column(
        "foods",
        sa.Column("energy", sa.Float(), nullable=False, server_default="0"),
    )
