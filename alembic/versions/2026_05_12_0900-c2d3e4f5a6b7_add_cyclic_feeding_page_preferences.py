"""add cyclic feeding page preferences

Revision ID: c2d3e4f5a6b7
Revises: b7c8d9e0f1a2
Create Date: 2026-05-12 09:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "last_valid_cyclic_feeding_configs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("line_id", sa.Uuid(), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("doser_id", sa.Uuid(), nullable=False),
        sa.Column("visits", sa.Integer(), nullable=False),
        sa.Column("blower_power_percentage", sa.Float(), nullable=False),
        sa.Column("cage_configs", sa.JSON(), nullable=False),
        sa.Column("updated_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["line_id"], ["feeding_lines.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_last_valid_cyclic_feeding_configs_line_id"),
        "last_valid_cyclic_feeding_configs",
        ["line_id"],
        unique=True,
    )

    op.create_table(
        "last_selected_feeding_modes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("line_id", sa.Uuid(), nullable=False),
        sa.Column("selected_mode", sa.String(length=20), nullable=False),
        sa.Column("updated_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["line_id"], ["feeding_lines.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_last_selected_feeding_modes_line_id"),
        "last_selected_feeding_modes",
        ["line_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_last_selected_feeding_modes_line_id"),
        table_name="last_selected_feeding_modes",
    )
    op.drop_table("last_selected_feeding_modes")
    op.drop_index(
        op.f("ix_last_valid_cyclic_feeding_configs_line_id"),
        table_name="last_valid_cyclic_feeding_configs",
    )
    op.drop_table("last_valid_cyclic_feeding_configs")
