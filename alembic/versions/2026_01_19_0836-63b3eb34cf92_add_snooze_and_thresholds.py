"""add snooze and thresholds

Revision ID: 63b3eb34cf92
Revises: 8f0g6b7c9d5e
Create Date: 2026-01-19 08:36:15.245230

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '63b3eb34cf92'
down_revision: Union[str, Sequence[str], None] = '8f0g6b7c9d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add snoozed_until column to alerts table
    op.add_column('alerts', sa.Column('snoozed_until', sa.DateTime(), nullable=True))
    
    # Add threshold columns to silos table
    op.add_column('silos', sa.Column('warning_threshold_percentage', sa.Float(), nullable=False, server_default='20.0'))
    op.add_column('silos', sa.Column('critical_threshold_percentage', sa.Float(), nullable=False, server_default='10.0'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove threshold columns from silos table
    op.drop_column('silos', 'critical_threshold_percentage')
    op.drop_column('silos', 'warning_threshold_percentage')
    
    # Remove snoozed_until column from alerts table
    op.drop_column('alerts', 'snoozed_until')
