"""create_alerts_tables

Revision ID: 4b7c9d2e8f1a
Revises: 3a8f2c1d5e6b
Create Date: 2026-01-16 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4b7c9d2e8f1a"
down_revision: Union[str, Sequence[str], None] = "3a8f2c1d5e6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crear tablas de alertas y alertas programadas."""
    # Tabla alerts
    op.create_table(
        "alerts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source", sa.String(200), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by", sa.String(100), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_type", "alerts", ["type"], unique=False)
    op.create_index("ix_alerts_status", "alerts", ["status"], unique=False)
    op.create_index("ix_alerts_category", "alerts", ["category"], unique=False)
    op.create_index("ix_alerts_timestamp", "alerts", ["timestamp"], unique=False)

    # Tabla scheduled_alerts
    op.create_table(
        "scheduled_alerts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("frequency", sa.String(), nullable=False),
        sa.Column("next_trigger_date", sa.DateTime(), nullable=False),
        sa.Column(
            "days_before_warning", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("device_id", sa.String(100), nullable=True),
        sa.Column("device_name", sa.String(200), nullable=True),
        sa.Column("custom_days_interval", sa.Integer(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_triggered_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_scheduled_alerts_next_trigger_date",
        "scheduled_alerts",
        ["next_trigger_date"],
        unique=False,
    )
    op.create_index(
        "ix_scheduled_alerts_is_active",
        "scheduled_alerts",
        ["is_active"],
        unique=False,
    )


def downgrade() -> None:
    """Eliminar tablas de alertas."""
    op.drop_index("ix_scheduled_alerts_is_active", table_name="scheduled_alerts")
    op.drop_index("ix_scheduled_alerts_next_trigger_date", table_name="scheduled_alerts")
    op.drop_table("scheduled_alerts")

    op.drop_index("ix_alerts_timestamp", table_name="alerts")
    op.drop_index("ix_alerts_category", table_name="alerts")
    op.drop_index("ix_alerts_status", table_name="alerts")
    op.drop_index("ix_alerts_type", table_name="alerts")
    op.drop_table("alerts")
