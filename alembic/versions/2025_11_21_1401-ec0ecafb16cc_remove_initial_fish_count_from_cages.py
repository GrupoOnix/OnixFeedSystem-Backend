"""remove_initial_fish_count_from_cages

Revision ID: ec0ecafb16cc
Revises: 483c40c16b03
Create Date: 2025-11-21 14:01:25.063668

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec0ecafb16cc'
down_revision: Union[str, Sequence[str], None] = '483c40c16b03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
