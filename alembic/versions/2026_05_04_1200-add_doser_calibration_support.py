"""add doser calibration support

Revision ID: add_doser_calibration
Revises: 6e27c787320e
Create Date: 2026-05-04 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_doser_calibration"
down_revision: Union[str, Sequence[str], None] = "6e27c787320e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("dosers", sa.Column("calibrated_grams_per_second", sa.Float(), nullable=True))
    op.add_column("dosers", sa.Column("pulse_on_time", sa.Float(), nullable=True))
    op.add_column("dosers", sa.Column("pulse_off_time", sa.Float(), nullable=True))
    op.add_column("dosers", sa.Column("pulse_speed", sa.Integer(), nullable=True))

    op.create_table(
        "doser_calibrations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("doser_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("grams_per_second", sa.Float(), nullable=False),
        sa.Column("method", sa.String(), nullable=False),
        sa.Column("sample_average_grams", sa.Float(), nullable=True),
        sa.Column("pulse_count", sa.Integer(), nullable=True),
        sa.Column("active_time_seconds", sa.Float(), nullable=True),
        sa.Column("target_grams", sa.Float(), nullable=True),
        sa.Column("runtime_seconds", sa.Float(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["doser_id"], ["dosers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_doser_calibrations_created_at"), "doser_calibrations", ["created_at"], unique=False)
    op.create_index(op.f("ix_doser_calibrations_doser_id"), "doser_calibrations", ["doser_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_doser_calibrations_doser_id"), table_name="doser_calibrations")
    op.drop_index(op.f("ix_doser_calibrations_created_at"), table_name="doser_calibrations")
    op.drop_table("doser_calibrations")
    op.drop_column("dosers", "pulse_speed")
    op.drop_column("dosers", "pulse_off_time")
    op.drop_column("dosers", "pulse_on_time")
    op.drop_column("dosers", "calibrated_grams_per_second")
