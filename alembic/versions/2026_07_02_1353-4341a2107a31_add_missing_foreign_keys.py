"""add_missing_foreign_keys

Revision ID: 4341a2107a31
Revises: 58a869207821
Create Date: 2026-07-02 13:53:10.604112

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '4341a2107a31'
down_revision: Union[str, Sequence[str], None] = '58a869207821'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Agrega foreign keys faltantes alineadas con los modelos SQLModel.
    """
    op.create_foreign_key(
        op.f("fk_feeding_sessions_line_id_feeding_lines"),
        "feeding_sessions",
        "feeding_lines",
        ["line_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_slot_assignments_line_id_feeding_lines"),
        "slot_assignments",
        "feeding_lines",
        ["line_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        op.f("fk_slot_assignments_cage_id_cages"),
        "slot_assignments",
        "cages",
        ["cage_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        op.f("fk_slot_assignments_cage_id_cages"),
        "slot_assignments",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_slot_assignments_line_id_feeding_lines"),
        "slot_assignments",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_feeding_sessions_line_id_feeding_lines"),
        "feeding_sessions",
        type_="foreignkey",
    )
