"""add FIFO silo inventory

Revision ID: f1a2b3c4d5e6
Revises: e1f2a3b4c5d6
Create Date: 2026-06-23 12:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "silo_inventory_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("silo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("food_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("remaining_quantity_mg", sa.BigInteger(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by_operator_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["food_id"], ["foods.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["silo_id"], ["silos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_silo_batches_fifo",
        "silo_inventory_batches",
        ["silo_id", "status", "position"],
        unique=False,
    )

    op.create_table(
        "silo_inventory_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("silo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("movement_type", sa.String(length=30), nullable=False),
        sa.Column("operator_id", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("quantity_delta_mg", sa.BigInteger(), nullable=False),
        sa.Column("previous_quantity_mg", sa.BigInteger(), nullable=False),
        sa.Column("new_quantity_mg", sa.BigInteger(), nullable=False),
        sa.Column("previous_food_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("new_food_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("previous_position", sa.Integer(), nullable=True),
        sa.Column("new_position", sa.Integer(), nullable=True),
        sa.Column("feeding_session_id", sa.String(), nullable=True),
        sa.Column("cage_feeding_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["silo_inventory_batches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cage_feeding_id"], ["cage_feedings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["feeding_session_id"], ["feeding_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["silo_id"], ["silos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_silo_inventory_movements_silo_created",
        "silo_inventory_movements",
        ["silo_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "silo_stock_reservations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feeding_session_id", sa.String(), nullable=False),
        sa.Column("silo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reserved_quantity_mg", sa.BigInteger(), nullable=False),
        sa.Column("consumed_quantity_mg", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["silo_inventory_batches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["feeding_session_id"], ["feeding_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["silo_id"], ["silos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_silo_reservations_session_status",
        "silo_stock_reservations",
        ["feeding_session_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_silo_reservations_batch_status",
        "silo_stock_reservations",
        ["batch_id", "status"],
        unique=False,
    )

    op.create_table(
        "feeding_batch_consumptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("feeding_session_id", sa.String(), nullable=False),
        sa.Column("cage_feeding_id", sa.String(), nullable=False),
        sa.Column("silo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("food_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity_mg", sa.BigInteger(), nullable=False),
        sa.Column("operator_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["silo_inventory_batches.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["cage_feeding_id"], ["cage_feedings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["feeding_session_id"], ["feeding_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["food_id"], ["foods.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["silo_id"], ["silos.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_feeding_batch_consumptions_session",
        "feeding_batch_consumptions",
        ["feeding_session_id"],
        unique=False,
    )
    op.create_index(
        "ix_feeding_batch_consumptions_batch",
        "feeding_batch_consumptions",
        ["batch_id"],
        unique=False,
    )
    op.create_index(
        "ix_feeding_batch_consumptions_food",
        "feeding_batch_consumptions",
        ["food_id"],
        unique=False,
    )

    # Deterministic UUIDs avoid requiring a PostgreSQL UUID extension.
    op.execute(
        """
        INSERT INTO silo_inventory_batches (
            id, silo_id, food_id, remaining_quantity_mg, position, status,
            received_at, created_by_operator_id, created_at, updated_at
        )
        SELECT
            md5(id::text || chr(58) || 'legacy-batch')::uuid,
            id,
            food_id,
            stock_level_mg,
            1,
            CASE WHEN stock_level_mg > 0 THEN 'ACTIVE' ELSE 'DEPLETED' END,
            created_at,
            'system:migration',
            created_at,
            NOW()
        FROM silos
        WHERE stock_level_mg > 0
        """
    )
    op.execute(
        """
        INSERT INTO silo_inventory_movements (
            id, silo_id, batch_id, movement_type, operator_id, reason,
            quantity_delta_mg, previous_quantity_mg, new_quantity_mg,
            previous_food_id, new_food_id, previous_position, new_position,
            created_at
        )
        SELECT
            md5(id::text || chr(58) || 'legacy-movement')::uuid,
            id,
            md5(id::text || chr(58) || 'legacy-batch')::uuid,
            'INITIAL_LOAD',
            'system:migration',
            'Migración desde stock_level_mg',
            stock_level_mg,
            0,
            stock_level_mg,
            NULL,
            food_id,
            NULL,
            1,
            NOW()
        FROM silos
        WHERE stock_level_mg > 0
        """
    )

    op.drop_constraint("fk_silos_food_id", "silos", type_="foreignkey")
    op.drop_column("silos", "food_id")
    op.drop_column("silos", "stock_level_mg")
    op.drop_column("silos", "is_assigned")


def downgrade() -> None:
    op.add_column("silos", sa.Column("is_assigned", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("silos", sa.Column("stock_level_mg", sa.BigInteger(), nullable=False, server_default="0"))
    op.add_column("silos", sa.Column("food_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_silos_food_id",
        "silos",
        "foods",
        ["food_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute(
        """
        UPDATE silos AS s
        SET stock_level_mg = inventory.total_mg,
            food_id = inventory.single_food_id
        FROM (
            SELECT
                silo_id,
                SUM(remaining_quantity_mg) AS total_mg,
                CASE
                    WHEN COUNT(DISTINCT food_id) = 1
                    THEN (array_agg(DISTINCT food_id))[1]
                    ELSE NULL
                END AS single_food_id
            FROM silo_inventory_batches
            WHERE status <> 'ARCHIVED'
            GROUP BY silo_id
        ) AS inventory
        WHERE s.id = inventory.silo_id
        """
    )
    op.execute(
        """
        UPDATE silos AS s
        SET is_assigned = EXISTS (
            SELECT 1 FROM doser_silos ds WHERE ds.silo_id = s.id
        )
        """
    )

    op.drop_index("ix_feeding_batch_consumptions_food", table_name="feeding_batch_consumptions")
    op.drop_index("ix_feeding_batch_consumptions_batch", table_name="feeding_batch_consumptions")
    op.drop_index("ix_feeding_batch_consumptions_session", table_name="feeding_batch_consumptions")
    op.drop_table("feeding_batch_consumptions")
    op.drop_index("ix_silo_reservations_batch_status", table_name="silo_stock_reservations")
    op.drop_index("ix_silo_reservations_session_status", table_name="silo_stock_reservations")
    op.drop_table("silo_stock_reservations")
    op.drop_index("ix_silo_inventory_movements_silo_created", table_name="silo_inventory_movements")
    op.drop_table("silo_inventory_movements")
    op.drop_index("ix_silo_batches_fifo", table_name="silo_inventory_batches")
    op.drop_table("silo_inventory_batches")
