"""add feeding execution jobs

Revision ID: 7e5d3c1a9b2f
Revises: a2c5d8e1f4b7
Create Date: 2026-08-27 12:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "7e5d3c1a9b2f"
down_revision: Union[str, None] = "a2c5d8e1f4b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feeding_execution_jobs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("feeding_session_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("worker_id", sa.String(length=255), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.String(length=1000), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["feeding_session_id"], ["feeding_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("feeding_session_id", name="uq_feeding_execution_jobs_session"),
    )
    op.create_index("ix_feeding_execution_jobs_status", "feeding_execution_jobs", ["status"])
    op.create_index("ix_feeding_execution_jobs_lease_expires_at", "feeding_execution_jobs", ["lease_expires_at"])
    op.create_index("ix_feeding_execution_jobs_created_at", "feeding_execution_jobs", ["created_at"])
    op.create_index("ix_feeding_execution_jobs_worker_id", "feeding_execution_jobs", ["worker_id"])


def downgrade() -> None:
    op.drop_index("ix_feeding_execution_jobs_worker_id", table_name="feeding_execution_jobs")
    op.drop_index("ix_feeding_execution_jobs_created_at", table_name="feeding_execution_jobs")
    op.drop_index("ix_feeding_execution_jobs_lease_expires_at", table_name="feeding_execution_jobs")
    op.drop_index("ix_feeding_execution_jobs_status", table_name="feeding_execution_jobs")
    op.drop_table("feeding_execution_jobs")
