"""convert all timestamps to timestamptz

Revision ID: f3a4b5c6d7e8
Revises: e7a46278866f
Create Date: 2026-02-17 12:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f3a4b5c6d7e8'
down_revision = 'e7a46278866f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convierte todas las columnas TIMESTAMP WITHOUT TIME ZONE a TIMESTAMPTZ
    # Se asume que los datos existentes están en UTC
    columns = [
        ("cage_biometry_log", "created_at"),
        ("cage_config_changes_log", "created_at"),
        ("cage_feedings", "created_at"),
        ("cage_groups", "created_at"),
        ("cage_groups", "updated_at"),
        ("cage_mortality_log", "created_at"),
        ("cage_population_events", "created_at"),
        ("cages", "created_at"),
        ("feeding_events", "timestamp"),
        ("feeding_lines", "created_at"),
        ("feeding_operations", "ended_at"),
        ("feeding_operations", "started_at"),
        ("feeding_sessions", "actual_end"),
        ("feeding_sessions", "actual_start"),
        ("feeding_sessions", "created_at"),
        ("feeding_sessions", "scheduled_start"),
        ("foods", "created_at"),
        ("foods", "updated_at"),
        ("operation_events", "timestamp"),
        ("silos", "created_at"),
        ("slot_assignments", "assigned_at"),
    ]

    for table, column in columns:
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN {column} "
            f"TYPE TIMESTAMP WITH TIME ZONE USING {column} AT TIME ZONE 'UTC'"
        )


def downgrade() -> None:
    columns = [
        ("cage_biometry_log", "created_at"),
        ("cage_config_changes_log", "created_at"),
        ("cage_feedings", "created_at"),
        ("cage_groups", "created_at"),
        ("cage_groups", "updated_at"),
        ("cage_mortality_log", "created_at"),
        ("cage_population_events", "created_at"),
        ("cages", "created_at"),
        ("feeding_events", "timestamp"),
        ("feeding_lines", "created_at"),
        ("feeding_operations", "ended_at"),
        ("feeding_operations", "started_at"),
        ("feeding_sessions", "actual_end"),
        ("feeding_sessions", "actual_start"),
        ("feeding_sessions", "created_at"),
        ("feeding_sessions", "scheduled_start"),
        ("foods", "created_at"),
        ("foods", "updated_at"),
        ("operation_events", "timestamp"),
        ("silos", "created_at"),
        ("slot_assignments", "assigned_at"),
    ]

    for table, column in columns:
        op.execute(
            f"ALTER TABLE {table} ALTER COLUMN {column} "
            f"TYPE TIMESTAMP WITHOUT TIME ZONE USING {column} AT TIME ZONE 'UTC'"
        )
