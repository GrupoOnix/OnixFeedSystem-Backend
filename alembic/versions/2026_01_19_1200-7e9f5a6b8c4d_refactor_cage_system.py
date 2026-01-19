"""Refactor cage system - new architecture

Revision ID: 7e9f5a6b8c4d
Revises: 6d8e4f5a9b3c
Create Date: 2026-01-19 12:00:00.000000

This migration:
1. Modifies the cages table to use the new simplified schema
2. Creates the cage_population_events table
3. Migrates existing data from old log tables to new events table
4. Removes old log tables (biometry, mortality, config changes)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "7e9f5a6b8c4d"
down_revision: Union[str, None] = "6d8e4f5a9b3c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==========================================================================
    # 1. Create new cage_population_events table
    # ==========================================================================
    op.create_table(
        "cage_population_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("fish_count_delta", sa.Integer(), nullable=False),
        sa.Column("new_fish_count", sa.Integer(), nullable=False),
        sa.Column("avg_weight_grams", sa.Float(), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cage_id"], ["cages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_cage_population_events_cage_id"),
        "cage_population_events",
        ["cage_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cage_population_events_created_at"),
        "cage_population_events",
        ["created_at"],
        unique=False,
    )

    # ==========================================================================
    # 2. Migrate data from old biometry logs to new events
    # ==========================================================================
    op.execute("""
        INSERT INTO cage_population_events (id, cage_id, event_type, event_date, fish_count_delta, new_fish_count, avg_weight_grams, note, created_at)
        SELECT
            biometry_id,
            cage_id,
            'BIOMETRY',
            sampling_date,
            COALESCE(new_fish_count, 0) - COALESCE(old_fish_count, 0),
            COALESCE(new_fish_count, 0),
            new_average_weight_g,
            note,
            created_at
        FROM cage_biometry_log
        WHERE new_average_weight_g IS NOT NULL OR new_fish_count IS NOT NULL
    """)

    # ==========================================================================
    # 3. Migrate data from old mortality logs to new events
    # ==========================================================================
    op.execute("""
        INSERT INTO cage_population_events (id, cage_id, event_type, event_date, fish_count_delta, new_fish_count, avg_weight_grams, note, created_at)
        SELECT
            mortality_id,
            cage_id,
            'MORTALITY',
            mortality_date,
            -dead_fish_count,
            0,  -- Will need to be recalculated based on cage current state
            NULL,
            note,
            created_at
        FROM cage_mortality_log
    """)

    # ==========================================================================
    # 4. Modify cages table - add new columns
    # ==========================================================================
    # First, update NULL values to 0
    op.execute(
        "UPDATE cages SET current_fish_count = 0 WHERE current_fish_count IS NULL"
    )

    # Rename current_fish_count to fish_count and make it NOT NULL with default 0
    op.alter_column(
        "cages",
        "current_fish_count",
        new_column_name="fish_count",
        existing_type=sa.Integer(),
        nullable=False,
        server_default="0",
    )

    # Rename avg_fish_weight_mg to avg_weight_grams (convert from mg to g)
    op.add_column("cages", sa.Column("avg_weight_grams", sa.Float(), nullable=True))
    op.execute(
        "UPDATE cages SET avg_weight_grams = avg_fish_weight_mg / 1000.0 WHERE avg_fish_weight_mg IS NOT NULL"
    )
    op.drop_column("cages", "avg_fish_weight_mg")

    # Rename total_volume_m3 to volume_m3
    op.alter_column(
        "cages",
        "total_volume_m3",
        new_column_name="volume_m3",
        existing_type=sa.Float(),
        existing_nullable=True,
    )

    # Rename transport_time_sec to transport_time_seconds
    op.alter_column(
        "cages",
        "transport_time_sec",
        new_column_name="transport_time_seconds",
        existing_type=sa.Integer(),
        existing_nullable=True,
    )

    # ==========================================================================
    # 5. Remove columns no longer needed (line assignment moved to FeedingLine)
    # ==========================================================================
    op.drop_constraint("cages_line_id_fkey", "cages", type_="foreignkey")
    op.drop_index("ix_cages_line_id", table_name="cages")
    op.drop_column("cages", "line_id")
    op.drop_column("cages", "slot_number")
    op.drop_column("cages", "feeding_table_id")

    # ==========================================================================
    # 6. Drop old log tables (after migration)
    # ==========================================================================
    op.drop_table("cage_config_changes_log")
    op.drop_table("cage_mortality_log")
    op.drop_table("cage_biometry_log")


def downgrade() -> None:
    # ==========================================================================
    # 1. Recreate old log tables
    # ==========================================================================
    op.create_table(
        "cage_biometry_log",
        sa.Column("biometry_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("old_fish_count", sa.Integer(), nullable=True),
        sa.Column("new_fish_count", sa.Integer(), nullable=True),
        sa.Column("old_average_weight_g", sa.Float(), nullable=True),
        sa.Column("new_average_weight_g", sa.Float(), nullable=True),
        sa.Column("sampling_date", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cage_id"], ["cages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("biometry_id"),
    )

    op.create_table(
        "cage_mortality_log",
        sa.Column("mortality_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dead_fish_count", sa.Integer(), nullable=False),
        sa.Column("mortality_date", sa.Date(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cage_id"], ["cages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("mortality_id"),
    )

    op.create_table(
        "cage_config_changes_log",
        sa.Column("change_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cage_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(length=50), nullable=False),
        sa.Column("old_value", sa.String(), nullable=False),
        sa.Column("new_value", sa.String(), nullable=False),
        sa.Column("change_reason", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cage_id"], ["cages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("change_id"),
    )

    # ==========================================================================
    # 2. Restore cages table columns
    # ==========================================================================
    op.add_column(
        "cages", sa.Column("feeding_table_id", sa.String(length=50), nullable=True)
    )
    op.add_column("cages", sa.Column("slot_number", sa.Integer(), nullable=True))
    op.add_column(
        "cages", sa.Column("line_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_index("ix_cages_line_id", "cages", ["line_id"], unique=False)
    op.create_foreign_key(
        "cages_line_id_fkey",
        "cages",
        "feeding_lines",
        ["line_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Restore column names
    op.alter_column(
        "cages",
        "transport_time_seconds",
        new_column_name="transport_time_sec",
        existing_type=sa.Integer(),
        existing_nullable=True,
    )

    op.alter_column(
        "cages",
        "volume_m3",
        new_column_name="total_volume_m3",
        existing_type=sa.Float(),
        existing_nullable=True,
    )

    # Restore avg_fish_weight_mg
    op.add_column("cages", sa.Column("avg_fish_weight_mg", sa.Integer(), nullable=True))
    op.execute(
        "UPDATE cages SET avg_fish_weight_mg = CAST(avg_weight_grams * 1000 AS INTEGER) WHERE avg_weight_grams IS NOT NULL"
    )
    op.drop_column("cages", "avg_weight_grams")

    # Restore fish_count to current_fish_count
    op.alter_column(
        "cages",
        "fish_count",
        new_column_name="current_fish_count",
        existing_type=sa.Integer(),
        nullable=True,
        server_default=None,
    )

    # ==========================================================================
    # 3. Drop new events table
    # ==========================================================================
    op.drop_index(
        op.f("ix_cage_population_events_created_at"),
        table_name="cage_population_events",
    )
    op.drop_index(
        op.f("ix_cage_population_events_cage_id"), table_name="cage_population_events"
    )
    op.drop_table("cage_population_events")
    op.drop_table("cage_population_events")
