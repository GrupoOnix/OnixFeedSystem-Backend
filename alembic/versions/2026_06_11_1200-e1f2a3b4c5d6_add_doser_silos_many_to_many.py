"""add doser silos many to many

Revision ID: e1f2a3b4c5d6
Revises: d4e5f6a7b8c9
Create Date: 2026-06-11 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "doser_silos",
        sa.Column("doser_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("silo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["doser_id"], ["dosers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["silo_id"], ["silos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("doser_id", "silo_id"),
    )
    op.create_index(
        op.f("ix_doser_silos_silo_id"),
        "doser_silos",
        ["silo_id"],
        unique=False,
    )

    op.execute(
        """
        INSERT INTO doser_silos (doser_id, silo_id)
        SELECT id, silo_id
        FROM dosers
        WHERE silo_id IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_doser_silos_silo_id"), table_name="doser_silos")
    op.drop_table("doser_silos")
