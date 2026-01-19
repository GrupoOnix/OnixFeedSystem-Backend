"""Create slot_assignments table

Revision ID: 8f0g6b7c9d5e
Revises: 7e9f5a6b8c4d
Create Date: 2026-01-19 14:00:00.000000

This migration creates the slot_assignments table to manage
the relationship between cages and feeding line slots.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "8f0g6b7c9d5e"
down_revision: Union[str, None] = "7e9f5a6b8c4d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "slot_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("line_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slot_number", sa.Integer(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["line_id"], ["feeding_lines.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cage_id"], ["cages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        # Unique constraint: one cage can only be in one slot
        sa.UniqueConstraint("cage_id", name="uq_slot_assignments_cage_id"),
        # Unique constraint: one slot per line can only have one cage
        sa.UniqueConstraint(
            "line_id", "slot_number", name="uq_slot_assignments_line_slot"
        ),
    )
    op.create_index(
        op.f("ix_slot_assignments_line_id"),
        "slot_assignments",
        ["line_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_slot_assignments_cage_id"),
        "slot_assignments",
        ["cage_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_slot_assignments_cage_id"), table_name="slot_assignments")
    op.drop_index(op.f("ix_slot_assignments_line_id"), table_name="slot_assignments")
    op.drop_table("slot_assignments")
