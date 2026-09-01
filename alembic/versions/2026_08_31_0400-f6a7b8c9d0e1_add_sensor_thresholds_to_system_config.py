"""add sensor thresholds to system config

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-08-31 04:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("system_config", sa.Column("temperature_warning_threshold", sa.Float(), nullable=False, server_default="70"))
    op.add_column("system_config", sa.Column("temperature_critical_threshold", sa.Float(), nullable=False, server_default="85"))
    op.add_column("system_config", sa.Column("pressure_warning_threshold", sa.Float(), nullable=False, server_default="1.3"))
    op.add_column("system_config", sa.Column("pressure_critical_threshold", sa.Float(), nullable=False, server_default="1.5"))
    op.add_column("system_config", sa.Column("flow_warning_threshold", sa.Float(), nullable=False, server_default="18"))
    op.add_column("system_config", sa.Column("flow_critical_threshold", sa.Float(), nullable=False, server_default="22"))


def downgrade() -> None:
    op.drop_column("system_config", "flow_critical_threshold")
    op.drop_column("system_config", "flow_warning_threshold")
    op.drop_column("system_config", "pressure_critical_threshold")
    op.drop_column("system_config", "pressure_warning_threshold")
    op.drop_column("system_config", "temperature_critical_threshold")
    op.drop_column("system_config", "temperature_warning_threshold")
