"""add_speed_percentage_to_dosers

Revision ID: 65946b59fe51
Revises: 7e23254e0ec0
Create Date: 2026-02-10 06:36:56.511029

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65946b59fe51'
down_revision: Union[str, Sequence[str], None] = '7e23254e0ec0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('dosers', sa.Column('speed_percentage', sa.Integer(), nullable=False, server_default='50'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('dosers', 'speed_percentage')
