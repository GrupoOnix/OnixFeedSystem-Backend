"""add selector_positioning_time_seconds to system_config

Revision ID: dfe5ac557bbd
Revises: 694997db23fe
Create Date: 2026-02-26 14:21:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "dfe5ac557bbd"
down_revision: Union[str, None] = "694997db23fe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "system_config",
        sa.Column(
            "selector_positioning_time_seconds",
            sa.Integer(),
            nullable=False,
            server_default="10",
        ),
    )


def downgrade() -> None:
    op.drop_column("system_config", "selector_positioning_time_seconds")
