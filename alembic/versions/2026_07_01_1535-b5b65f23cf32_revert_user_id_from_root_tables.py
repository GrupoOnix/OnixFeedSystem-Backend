"""revert user_id from root tables

Revision ID: b5b65f23cf32
Revises: f1a2b3c4d5e6
Create Date: 2026-07-01 15:35:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b5b65f23cf32"
down_revision: Union[str, Sequence[str], None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Elimina las columnas user_id agregadas por la migración errónea."""
    op.execute(
        """
        DO $$
        DECLARE
            tables TEXT[] := ARRAY[
                'alerts', 'cage_groups', 'cages', 'feedback',
                'feeding_lines', 'feeding_sessions', 'foods',
                'scheduled_alerts', 'silos', 'slot_assignments',
                'system_config'
            ];
            t TEXT;
            fk_name TEXT;
        BEGIN
            -- Eliminar foreign keys hacia users que puedan existir
            FOREACH t IN ARRAY tables LOOP
                FOR fk_name IN
                    SELECT tc.constraint_name
                    FROM information_schema.table_constraints tc
                    WHERE tc.table_name = t
                      AND tc.constraint_type = 'FOREIGN KEY'
                      AND tc.table_schema = CURRENT_SCHEMA()
                LOOP
                    EXECUTE format(
                        'ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I',
                        t, fk_name
                    );
                END LOOP;
            END LOOP;

            -- Eliminar columnas user_id
            FOREACH t IN ARRAY tables LOOP
                EXECUTE format(
                    'ALTER TABLE %I DROP COLUMN IF EXISTS user_id',
                    t
                );
            END LOOP;
        END $$;
        """
    )

    # Restaurar constraints únicos originales (sin user_id)
    op.execute(
        """
        DO $$
        BEGIN
            ALTER TABLE cage_groups
                DROP CONSTRAINT IF EXISTS uq_cage_groups_name_user;
            ALTER TABLE cage_groups
                DROP CONSTRAINT IF EXISTS cage_groups_name_key;
            ALTER TABLE cage_groups
                ADD CONSTRAINT cage_groups_name_key UNIQUE (name);

            ALTER TABLE cages
                DROP CONSTRAINT IF EXISTS uq_cages_name_user;
            ALTER TABLE cages
                DROP CONSTRAINT IF EXISTS cages_name_key;
            ALTER TABLE cages
                ADD CONSTRAINT cages_name_key UNIQUE (name);

            ALTER TABLE feeding_lines
                DROP CONSTRAINT IF EXISTS uq_feeding_lines_name_user;
            ALTER TABLE feeding_lines
                DROP CONSTRAINT IF EXISTS feeding_lines_name_key;
            ALTER TABLE feeding_lines
                ADD CONSTRAINT feeding_lines_name_key UNIQUE (name);

            ALTER TABLE foods
                DROP CONSTRAINT IF EXISTS uq_foods_name_user;
            ALTER TABLE foods
                DROP CONSTRAINT IF EXISTS uq_foods_code_user;
            ALTER TABLE foods
                DROP CONSTRAINT IF EXISTS foods_name_key;
            ALTER TABLE foods
                DROP CONSTRAINT IF EXISTS foods_code_key;
            ALTER TABLE foods
                ADD CONSTRAINT foods_name_key UNIQUE (name);
            ALTER TABLE foods
                ADD CONSTRAINT foods_code_key UNIQUE (code);

            ALTER TABLE silos
                DROP CONSTRAINT IF EXISTS uq_silos_name_user;
            ALTER TABLE silos
                DROP CONSTRAINT IF EXISTS silos_name_key;
            ALTER TABLE silos
                ADD CONSTRAINT silos_name_key UNIQUE (name);

            ALTER TABLE system_config
                DROP CONSTRAINT IF EXISTS uq_system_config_user;
        END $$;
        """
    )

    # Eliminar índices que pudieran haber quedado
    op.execute(
        """
        DO $$
        BEGIN
            DROP INDEX IF EXISTS ix_alerts_user_id;
            DROP INDEX IF EXISTS ix_cage_groups_user_id;
            DROP INDEX IF EXISTS ix_cages_user_id;
            DROP INDEX IF EXISTS ix_feedback_user_id;
            DROP INDEX IF EXISTS ix_feeding_lines_user_id;
            DROP INDEX IF EXISTS ix_feeding_sessions_user_id;
            DROP INDEX IF EXISTS ix_foods_user_id;
            DROP INDEX IF EXISTS ix_scheduled_alerts_user_id;
            DROP INDEX IF EXISTS ix_silos_user_id;
            DROP INDEX IF EXISTS ix_slot_assignments_user_id;
            DROP INDEX IF EXISTS ix_system_config_user_id;
        END $$;
        """
    )


def downgrade() -> None:
    """No se recupera la migración errónea; se mantiene el esquema limpio."""
    pass
