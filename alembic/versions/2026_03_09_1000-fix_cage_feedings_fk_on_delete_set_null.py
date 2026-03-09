"""fix cage_feedings doser_id and silo_id fk on delete set null

Revision ID: fix_cage_feedings_fk
Revises: dfe5ac557bbd
Create Date: 2026-03-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fix_cage_feedings_fk'
down_revision: Union[str, Sequence[str], None] = '720a03b05d34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix cage_feedings FK constraints to use ON DELETE SET NULL."""
    # Drop existing FK constraints
    op.drop_constraint('cage_feedings_doser_id_fkey', 'cage_feedings', type_='foreignkey')
    op.drop_constraint('cage_feedings_silo_id_fkey', 'cage_feedings', type_='foreignkey')

    # Recreate with ON DELETE SET NULL
    op.create_foreign_key(
        'cage_feedings_doser_id_fkey',
        'cage_feedings', 'dosers',
        ['doser_id'], ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'cage_feedings_silo_id_fkey',
        'cage_feedings', 'silos',
        ['silo_id'], ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    """Revert FK constraints to no on-delete action."""
    op.drop_constraint('cage_feedings_doser_id_fkey', 'cage_feedings', type_='foreignkey')
    op.drop_constraint('cage_feedings_silo_id_fkey', 'cage_feedings', type_='foreignkey')

    op.create_foreign_key(None, 'cage_feedings', 'dosers', ['doser_id'], ['id'])
    op.create_foreign_key(None, 'cage_feedings', 'silos', ['silo_id'], ['id'])
