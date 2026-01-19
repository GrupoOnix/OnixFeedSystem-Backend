"""add is_on to doser

Revision ID: 3a8f2c1d5e6b
Revises: 897baf33d221
Create Date: 2026-01-16 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3a8f2c1d5e6b"
down_revision: Union[str, Sequence[str], None] = "897baf33d221"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Agregar columna is_on con default True para dosers existentes
    op.add_column(
        "dosers",
        sa.Column("is_on", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("dosers", "is_on")
