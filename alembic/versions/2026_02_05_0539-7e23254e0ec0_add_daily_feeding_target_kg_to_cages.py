"""add daily_feeding_target_kg to cages

Revision ID: 7e23254e0ec0
Revises: 096de1908851
Create Date: 2026-02-05 05:39:08.929646

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7e23254e0ec0"
down_revision: Union[str, Sequence[str], None] = "096de1908851"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("cages", sa.Column("daily_feeding_target_kg", sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("cages", "daily_feeding_target_kg")
