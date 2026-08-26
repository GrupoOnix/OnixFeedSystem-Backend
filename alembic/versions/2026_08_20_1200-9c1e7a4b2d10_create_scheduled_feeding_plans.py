"""create scheduled feeding plans

Revision ID: 9c1e7a4b2d10
Revises: 304a062a727a
Create Date: 2026-08-20 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9c1e7a4b2d10"
down_revision: Union[str, Sequence[str], None] = "304a062a727a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scheduled_feeding_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("line_id", sa.Uuid(), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("doser_id", sa.Uuid(), nullable=False),
        sa.Column("silo_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("start_time", sa.String(length=5), nullable=False),
        sa.Column("end_time", sa.String(length=5), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="America/Santiago"),
        sa.Column("blower_power_percentage", sa.Float(), nullable=False, server_default="70"),
        sa.Column("wait_after_visit_seconds", sa.Float(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("total_rounds", sa.Integer(), nullable=False),
        sa.Column("total_requested_kg", sa.Float(), nullable=False),
        sa.Column("total_planned_kg", sa.Float(), nullable=False),
        sa.Column("estimated_total_seconds", sa.Float(), nullable=False),
        sa.Column("cage_plans", sa.JSON(), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_name", sa.String(length=100), nullable=True),
        sa.Column("last_run_on", sa.String(length=10), nullable=True),
        sa.Column("last_session_id", sa.String(length=36), nullable=True),
        sa.Column("last_error", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["line_id"], ["feeding_lines.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_scheduled_feeding_plans_line_start",
        "scheduled_feeding_plans",
        ["line_id", "start_time"],
        unique=False,
    )
    op.add_column("cage_feedings", sa.Column("visit_quantities_kg", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("cage_feedings", "visit_quantities_kg")
    op.drop_index("ix_scheduled_feeding_plans_line_start", table_name="scheduled_feeding_plans")
    op.drop_table("scheduled_feeding_plans")
