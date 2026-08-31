"""add durable pulse doser calibration sessions

Revision ID: a8d5c9f0e241
Revises: 4b8f2d6c1e9a
Create Date: 2026-08-30 21:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "a8d5c9f0e241"
down_revision: Union[str, None] = "4b8f2d6c1e9a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("system_config", sa.Column("doser_calibration_tolerance_percentage", sa.Float(), nullable=False, server_default="5"))
    op.add_column("system_config", sa.Column("doser_calibration_max_pulses", sa.Integer(), nullable=False, server_default="10"))
    op.add_column("system_config", sa.Column("doser_calibration_max_attempt_seconds", sa.Integer(), nullable=False, server_default="20"))
    op.add_column("doser_calibrations", sa.Column("status", sa.String(length=32), nullable=False, server_default="VERIFIED"))
    op.add_column("doser_calibrations", sa.Column("food_id", sa.Uuid(), nullable=True))
    op.add_column("doser_calibrations", sa.Column("speed_percentage", sa.Integer(), nullable=True))
    op.add_column("doser_calibrations", sa.Column("pulse_on_time", sa.Float(), nullable=True))
    op.add_column("doser_calibrations", sa.Column("pulse_off_time", sa.Float(), nullable=True))
    op.add_column("doser_calibrations", sa.Column("tolerance_percentage", sa.Float(), nullable=True))
    op.add_column("doser_calibrations", sa.Column("included_attempts", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("doser_calibrations", sa.Column("restored_from_id", sa.Uuid(), nullable=True))
    op.create_index("ix_doser_calibrations_status", "doser_calibrations", ["status"])
    op.create_foreign_key("fk_doser_calibrations_food", "doser_calibrations", "foods", ["food_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_doser_calibrations_restored_from", "doser_calibrations", "doser_calibrations", ["restored_from_id"], ["id"], ondelete="SET NULL")

    op.create_table(
        "doser_calibration_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("doser_id", sa.Uuid(), nullable=False),
        sa.Column("line_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("target_grams", sa.Float(), nullable=False),
        sa.Column("pulse_on_time", sa.Float(), nullable=False),
        sa.Column("pulse_off_time", sa.Float(), nullable=False),
        sa.Column("speed_percentage", sa.Integer(), nullable=False),
        sa.Column("tolerance_percentage", sa.Float(), nullable=False),
        sa.Column("food_id", sa.Uuid(), nullable=True),
        sa.Column("started_by", sa.String(length=100), nullable=False),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("final_calibration_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["doser_id"], ["dosers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["line_id"], ["feeding_lines.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["food_id"], ["foods.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["final_calibration_id"], ["doser_calibrations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_doser_calibration_sessions_doser_id", "doser_calibration_sessions", ["doser_id"])
    op.create_index("ix_doser_calibration_sessions_line_id", "doser_calibration_sessions", ["line_id"])
    op.create_index("ix_doser_calibration_sessions_status", "doser_calibration_sessions", ["status"])

    op.create_table(
        "doser_calibration_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
        sa.Column("pulse_count", sa.Integer(), nullable=False),
        sa.Column("active_time_seconds", sa.Float(), nullable=False),
        sa.Column("expected_grams", sa.Float(), nullable=True),
        sa.Column("measured_grams", sa.Float(), nullable=True),
        sa.Column("error_percentage", sa.Float(), nullable=True),
        sa.Column("included", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["doser_calibration_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "sequence", name="uq_doser_calibration_attempt_sequence"),
    )
    op.create_index("ix_doser_calibration_attempts_session_id", "doser_calibration_attempts", ["session_id"])
    op.create_index("ix_doser_calibration_attempts_status", "doser_calibration_attempts", ["status"])


def downgrade() -> None:
    op.drop_column("system_config", "doser_calibration_max_attempt_seconds")
    op.drop_column("system_config", "doser_calibration_max_pulses")
    op.drop_column("system_config", "doser_calibration_tolerance_percentage")
    op.drop_index("ix_doser_calibration_attempts_status", table_name="doser_calibration_attempts")
    op.drop_index("ix_doser_calibration_attempts_session_id", table_name="doser_calibration_attempts")
    op.drop_table("doser_calibration_attempts")
    op.drop_index("ix_doser_calibration_sessions_status", table_name="doser_calibration_sessions")
    op.drop_index("ix_doser_calibration_sessions_line_id", table_name="doser_calibration_sessions")
    op.drop_index("ix_doser_calibration_sessions_doser_id", table_name="doser_calibration_sessions")
    op.drop_table("doser_calibration_sessions")
    op.drop_constraint("fk_doser_calibrations_restored_from", "doser_calibrations", type_="foreignkey")
    op.drop_constraint("fk_doser_calibrations_food", "doser_calibrations", type_="foreignkey")
    op.drop_index("ix_doser_calibrations_status", table_name="doser_calibrations")
    for name in ("restored_from_id", "included_attempts", "tolerance_percentage", "pulse_off_time", "pulse_on_time", "speed_percentage", "food_id", "status"):
        op.drop_column("doser_calibrations", name)
