"""add scheduled feeding runs

Revision ID: 4b8f2d6c1e9a
Revises: 7e5d3c1a9b2f
Create Date: 2026-08-27 13:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "4b8f2d6c1e9a"
down_revision: Union[str, None] = "7e5d3c1a9b2f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scheduled_feeding_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("run_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="CLAIMED"),
        sa.Column("worker_id", sa.String(length=255), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("session_id", sa.String(length=36), nullable=True),
        sa.Column("error", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["scheduled_feeding_plans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plan_id", "run_date", name="uq_scheduled_feeding_runs_plan_date"),
    )
    op.create_index("ix_scheduled_feeding_runs_plan_id", "scheduled_feeding_runs", ["plan_id"])
    op.create_index("ix_scheduled_feeding_runs_run_date", "scheduled_feeding_runs", ["run_date"])
    op.create_index("ix_scheduled_feeding_runs_status", "scheduled_feeding_runs", ["status"])
    op.create_index("ix_scheduled_feeding_runs_lease_expires_at", "scheduled_feeding_runs", ["lease_expires_at"])
    op.create_index("ix_scheduled_feeding_runs_session_id", "scheduled_feeding_runs", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_scheduled_feeding_runs_session_id", table_name="scheduled_feeding_runs")
    op.drop_index("ix_scheduled_feeding_runs_lease_expires_at", table_name="scheduled_feeding_runs")
    op.drop_index("ix_scheduled_feeding_runs_status", table_name="scheduled_feeding_runs")
    op.drop_index("ix_scheduled_feeding_runs_run_date", table_name="scheduled_feeding_runs")
    op.drop_index("ix_scheduled_feeding_runs_plan_id", table_name="scheduled_feeding_runs")
    op.drop_table("scheduled_feeding_runs")
