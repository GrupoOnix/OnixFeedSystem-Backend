"""add_feeding_sessions_and_events

Revision ID: fc42627a436f
Revises: e4da87a064dc
Create Date: 2025-11-27 16:18:29.664286

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fc42627a436f'
down_revision: Union[str, Sequence[str], None] = 'e4da87a064dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create feeding_sessions table
    op.create_table('feeding_sessions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('line_id', sa.Uuid(), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('total_dispensed_kg', sa.Float(), nullable=False),
    sa.Column('dispensed_by_slot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('applied_strategy_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['line_id'], ['feeding_lines.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for feeding_sessions
    op.create_index(op.f('ix_feeding_sessions_line_id'), 'feeding_sessions', ['line_id'], unique=False)
    op.create_index(op.f('ix_feeding_sessions_date'), 'feeding_sessions', ['date'], unique=False)
    op.create_index(op.f('ix_feeding_sessions_status'), 'feeding_sessions', ['status'], unique=False)
    
    # Create feeding_events table
    op.create_table('feeding_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Uuid(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('event_type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['session_id'], ['feeding_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for feeding_events
    op.create_index(op.f('ix_feeding_events_session_id'), 'feeding_events', ['session_id'], unique=False)
    op.create_index(op.f('ix_feeding_events_timestamp'), 'feeding_events', ['timestamp'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_index(op.f('ix_feeding_events_timestamp'), table_name='feeding_events')
    op.drop_index(op.f('ix_feeding_events_session_id'), table_name='feeding_events')
    op.drop_table('feeding_events')
    
    op.drop_index(op.f('ix_feeding_sessions_status'), table_name='feeding_sessions')
    op.drop_index(op.f('ix_feeding_sessions_date'), table_name='feeding_sessions')
    op.drop_index(op.f('ix_feeding_sessions_line_id'), table_name='feeding_sessions')
    op.drop_table('feeding_sessions')
