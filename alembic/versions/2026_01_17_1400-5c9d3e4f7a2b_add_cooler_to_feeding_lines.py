"""add_cooler_to_feeding_lines

Revision ID: 5c9d3e4f7a2b
Revises: 4b7c9d2e8f1a
Create Date: 2026-01-17 14:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5c9d3e4f7a2b"
down_revision: Union[str, Sequence[str], None] = "4b7c9d2e8f1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crear tabla coolers para el componente de enfriamiento de aire."""
    op.create_table(
        "coolers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("line_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_on", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cooling_power_percentage", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["line_id"],
            ["feeding_lines.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Eliminar tabla coolers."""
    op.drop_table("coolers")
