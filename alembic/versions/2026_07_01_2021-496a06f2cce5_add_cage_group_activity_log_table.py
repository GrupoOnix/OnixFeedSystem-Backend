"""add cage_group_activity_log table

Revision ID: 496a06f2cce5
Revises: 08b43ca26a82
Create Date: 2026-07-01 20:21:15.254510

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "496a06f2cce5"
down_revision: Union[str, Sequence[str], None] = "08b43ca26a82"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "cage_group_activity_log",
        sa.Column("log_id", sa.Uuid(), nullable=False),
        sa.Column("cage_group_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("category", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("message", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("details", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("actor", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["cage_group_id"], ["cage_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("log_id"),
    )
    op.create_index(
        op.f("ix_cage_group_activity_log_cage_group_id"), "cage_group_activity_log", ["cage_group_id"], unique=False
    )
    op.create_index(op.f("ix_cage_group_activity_log_category"), "cage_group_activity_log", ["category"], unique=False)
    op.create_index(op.f("ix_cage_group_activity_log_event_at"), "cage_group_activity_log", ["event_at"], unique=False)
    op.create_index(
        op.f("ix_cage_group_activity_log_event_type"), "cage_group_activity_log", ["event_type"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_cage_group_activity_log_event_type"), table_name="cage_group_activity_log")
    op.drop_index(op.f("ix_cage_group_activity_log_event_at"), table_name="cage_group_activity_log")
    op.drop_index(op.f("ix_cage_group_activity_log_category"), table_name="cage_group_activity_log")
    op.drop_index(op.f("ix_cage_group_activity_log_cage_group_id"), table_name="cage_group_activity_log")
    op.drop_table("cage_group_activity_log")
