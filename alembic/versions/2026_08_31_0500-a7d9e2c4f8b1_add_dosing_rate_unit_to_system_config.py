"""add global dosing rate display unit to system config

Revision ID: a7d9e2c4f8b1
Revises: f6a7b8c9d0e1
Create Date: 2026-08-31 05:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "a7d9e2c4f8b1"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("system_config", sa.Column("dosing_rate_unit", sa.String(length=10), nullable=False, server_default="kg/min"))


def downgrade() -> None:
    op.drop_column("system_config", "dosing_rate_unit")
