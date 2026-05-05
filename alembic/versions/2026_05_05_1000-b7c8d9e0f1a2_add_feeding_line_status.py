"""add feeding line status

Revision ID: b7c8d9e0f1a2
Revises: 9c1d2e3f4a5b
Create Date: 2026-05-05 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "9c1d2e3f4a5b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "feeding_lines",
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="AVAILABLE",
        ),
    )
    op.add_column(
        "feeding_lines",
        sa.Column("locked_by", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "feeding_lines",
        sa.Column("locked_reason", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "feeding_lines",
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("feeding_lines", "status", server_default=None)


def downgrade() -> None:
    op.drop_column("feeding_lines", "locked_at")
    op.drop_column("feeding_lines", "locked_reason")
    op.drop_column("feeding_lines", "locked_by")
    op.drop_column("feeding_lines", "status")
