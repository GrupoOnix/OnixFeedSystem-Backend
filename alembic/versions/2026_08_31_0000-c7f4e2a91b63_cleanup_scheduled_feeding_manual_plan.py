"""cleanup scheduled feeding for operator-started daily plans

Revision ID: c7f4e2a91b63
Revises: a8d5c9f0e241
Create Date: 2026-08-31 00:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c7f4e2a91b63"
down_revision: Union[str, None] = "a8d5c9f0e241"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "feeding_sessions",
        sa.Column("execution_context", sa.JSON(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_scheduled_feeding_plans_line_id",
        "scheduled_feeding_plans",
        ["line_id"],
    )
    op.drop_table("scheduled_feeding_runs")
    op.drop_column("scheduled_feeding_plans", "last_error")
    op.drop_column("scheduled_feeding_plans", "is_active")


def downgrade() -> None:
    op.add_column(
        "scheduled_feeding_plans",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "scheduled_feeding_plans",
        sa.Column("last_error", sa.String(length=500), nullable=True),
    )
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
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["scheduled_feeding_plans.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "plan_id",
            "run_date",
            name="uq_scheduled_feeding_runs_plan_date",
        ),
    )
    op.create_index(
        "ix_scheduled_feeding_runs_plan_id",
        "scheduled_feeding_runs",
        ["plan_id"],
    )
    op.create_index(
        "ix_scheduled_feeding_runs_run_date",
        "scheduled_feeding_runs",
        ["run_date"],
    )
    op.create_index(
        "ix_scheduled_feeding_runs_status",
        "scheduled_feeding_runs",
        ["status"],
    )
    op.create_index(
        "ix_scheduled_feeding_runs_lease_expires_at",
        "scheduled_feeding_runs",
        ["lease_expires_at"],
    )
    op.create_index(
        "ix_scheduled_feeding_runs_session_id",
        "scheduled_feeding_runs",
        ["session_id"],
    )
    op.drop_constraint(
        "uq_scheduled_feeding_plans_line_id",
        "scheduled_feeding_plans",
        type_="unique",
    )
    op.drop_column("feeding_sessions", "execution_context")
