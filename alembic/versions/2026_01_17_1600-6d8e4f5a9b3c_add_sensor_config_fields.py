"""add sensor config fields

Revision ID: 6d8e4f5a9b3c
Revises: 5c9d3e4f7a2b
Create Date: 2026-01-17 16:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6d8e4f5a9b3c"
down_revision: Union[str, None] = "5c9d3e4f7a2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sensors",
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "sensors",
        sa.Column("warning_threshold", sa.Float(), nullable=True),
    )
    op.add_column(
        "sensors",
        sa.Column("critical_threshold", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sensors", "critical_threshold")
    op.drop_column("sensors", "warning_threshold")
    op.drop_column("sensors", "is_enabled")
