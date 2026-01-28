"""add blower_power to cages

Revision ID: 096de1908851
Revises: 757cae81d594
Create Date: 2026-01-26 10:25:46.747421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '096de1908851'
down_revision: Union[str, Sequence[str], None] = '757cae81d594'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('cages', sa.Column('blower_power', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('cages', 'blower_power')
