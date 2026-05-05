"""add last valid manual feeding configs

Revision ID: 9c1d2e3f4a5b
Revises: add_doser_calibration
Create Date: 2026-05-04 15:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9c1d2e3f4a5b"
down_revision: Union[str, Sequence[str], None] = "add_doser_calibration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "last_valid_manual_feeding_configs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("line_id", sa.Uuid(), nullable=False),
        sa.Column("target_silo_id", sa.Uuid(), nullable=False),
        sa.Column("target_cage_id", sa.Uuid(), nullable=False),
        sa.Column("target_amount_kg", sa.Float(), nullable=False),
        sa.Column("dosing_rate_kg_per_min", sa.Float(), nullable=False),
        sa.Column("dosing_unit", sa.String(length=50), nullable=False),
        sa.Column("blower_power_percentage", sa.Float(), nullable=False),
        sa.Column("updated_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["line_id"], ["feeding_lines.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_last_valid_manual_feeding_configs_line_id"),
        "last_valid_manual_feeding_configs",
        ["line_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_last_valid_manual_feeding_configs_line_id"),
        table_name="last_valid_manual_feeding_configs",
    )
    op.drop_table("last_valid_manual_feeding_configs")
