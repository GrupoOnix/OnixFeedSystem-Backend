"""add user_id to 11 root tables

Revision ID: 720a03b05d34
Revises: dfe5ac557bbd
Create Date: 2026-03-02 14:27:45.624560

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = '720a03b05d34'
down_revision: Union[str, Sequence[str], None] = 'dfe5ac557bbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Migración errónea neutralizada. Agregaba columnas user_id con FK a una
    # tabla users que aún no existía, por lo que fallaba en entornos limpios.
    # La eliminación de estas columnas se realiza en la migración posterior
    # `revert_user_id_from_root_tables`.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # No-op: la migración de revertido se encarga de dejar el esquema limpio.
    pass
