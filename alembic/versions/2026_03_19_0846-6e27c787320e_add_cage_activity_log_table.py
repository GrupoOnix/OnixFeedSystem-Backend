"""add cage_activity_log table

Revision ID: 6e27c787320e
Revises: fix_cage_feedings_fk
Create Date: 2026-03-19 08:46:00.887326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6e27c787320e'
down_revision: Union[str, Sequence[str], None] = 'fix_cage_feedings_fk'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'cage_activity_log',
        sa.Column('log_id', sa.Uuid(), nullable=False),
        sa.Column('cage_id', sa.Uuid(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('details', sa.String(), nullable=True),
        sa.Column('actor', sa.String(), nullable=True),
        sa.Column('source_entity_type', sa.String(), nullable=True),
        sa.Column('source_entity_id', sa.String(), nullable=True),
        sa.Column('event_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['cage_id'], ['cages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('log_id'),
    )
    op.create_index(op.f('ix_cage_activity_log_cage_id'), 'cage_activity_log', ['cage_id'], unique=False)
    op.create_index(op.f('ix_cage_activity_log_category'), 'cage_activity_log', ['category'], unique=False)
    op.create_index(op.f('ix_cage_activity_log_event_at'), 'cage_activity_log', ['event_at'], unique=False)
    op.create_index(op.f('ix_cage_activity_log_event_type'), 'cage_activity_log', ['event_type'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_cage_activity_log_event_type'), table_name='cage_activity_log')
    op.drop_index(op.f('ix_cage_activity_log_event_at'), table_name='cage_activity_log')
    op.drop_index(op.f('ix_cage_activity_log_category'), table_name='cage_activity_log')
    op.drop_index(op.f('ix_cage_activity_log_cage_id'), table_name='cage_activity_log')
    op.drop_table('cage_activity_log')
