"""make_users_username_index_unique

Revision ID: 58a869207821
Revises: 496a06f2cce5
Create Date: 2026-07-02 13:39:53.222510

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '58a869207821'
down_revision: Union[str, Sequence[str], None] = '496a06f2cce5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Alinea la tabla users con UserModel:
    - username debe tener un índice único (unique=True, index=True).
    - Elimina el UniqueConstraint separado creado por la migración original,
      dejando solo el índice único.
    """
    # Eliminar el índice no único creado por la migración original.
    op.drop_index(op.f("ix_users_username"), table_name="users")

    # Eliminar el UniqueConstraint redundante sobre username si existe.
    # Se busca dinámicamente porque el nombre puede variar según la base.
    op.execute(
        """
        DO $$
        DECLARE
            constraint_name text;
        BEGIN
            SELECT conname INTO constraint_name
            FROM pg_constraint
            WHERE conrelid = 'users'::regclass
              AND contype = 'u'
              AND conkey @> ARRAY(
                  SELECT attnum
                  FROM pg_attribute
                  WHERE attrelid = 'users'::regclass
                    AND attname = 'username'
              );

            IF constraint_name IS NOT NULL THEN
                EXECUTE format('ALTER TABLE users DROP CONSTRAINT %I', constraint_name);
            END IF;
        END $$;
        """
    )

    # Crear el índice único que refleja Field(unique=True, index=True).
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)


def downgrade() -> None:
    """Downgrade schema.

    Restaura el estado anterior: índice no único + UniqueConstraint separado.
    """
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.create_index("ix_users_username", "users", ["username"], unique=False)
    op.create_unique_constraint("users_username_key", "users", ["username"])
