import asyncio
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text

# Cargar .env desde la raíz del proyecto
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from infrastructure.persistence.database import async_engine

async def verify():
    async with async_engine.begin() as conn:
        print("\n=== VERIFICACIÓN POST-MIGRACIÓN ===\n")

        # 1. Tabla slot_assignments eliminada
        result = await conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'slot_assignments')"
        ))
        exists = result.scalar()
        print(f"1. Tabla slot_assignments existe: {exists}")
        print(f"   {'❌ ERROR' if exists else '✅ Eliminada correctamente'}\n")

        # 2. Columnas nuevas en cages
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'cages' AND column_name IN ('line_id', 'slot_number')
            ORDER BY column_name
        """))
        columns = result.fetchall()
        print("2. Nuevas columnas en cages:")
        for col in columns:
            print(f"   - {col[0]} ({col[1]}, nullable={col[2]})")
        print(f"   {'✅ Creadas correctamente' if len(columns) == 2 else '❌ ERROR'}\n")

        # 3. Datos migrados
        result = await conn.execute(text("SELECT COUNT(*) FROM cages WHERE line_id IS NOT NULL"))
        with_line = result.scalar()
        result = await conn.execute(text("SELECT COUNT(*) FROM cages"))
        total = result.scalar()
        print(f"3. Datos migrados: {with_line}/{total} cages con line_id")
        print(f"   {'✅ Migración completada' if with_line > 0 else '⚠️  Sin datos (normal si no había slot_assignments)'}\n")

        # 4. Índice creado
        result = await conn.execute(text("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'cages' AND indexname = 'ix_cages_line_id'
        """))
        index = result.fetchone()
        print(f"4. Índice ix_cages_line_id: {'✅ Creado' if index else '❌ No encontrado'}\n")

        # 5. FK con SET NULL
        result = await conn.execute(text("""
            SELECT delete_rule FROM information_schema.referential_constraints rc
            JOIN information_schema.table_constraints tc ON rc.constraint_name = tc.constraint_name
            WHERE tc.table_name = 'cages' AND tc.constraint_type = 'FOREIGN KEY'
              AND rc.constraint_name LIKE '%line_id%'
        """))
        fk = result.fetchone()
        if fk:
            print(f"5. FK cages.line_id: DELETE {fk[0]}")
            print(f"   {'✅ Configurada correctamente' if fk[0] == 'SET NULL' else '⚠️  No es SET NULL'}\n")
        else:
            print("5. FK cages.line_id: ❌ No encontrada\n")

        # 6. CASCADE en logs
        result = await conn.execute(text("""
            SELECT tc.table_name, rc.delete_rule
            FROM information_schema.referential_constraints rc
            JOIN information_schema.table_constraints tc ON rc.constraint_name = tc.constraint_name
            WHERE tc.table_name IN ('cage_biometry_log', 'cage_mortality_log', 'cage_config_changes_log')
              AND rc.delete_rule = 'CASCADE'
            ORDER BY tc.table_name
        """))
        cascades = result.fetchall()
        print("6. CASCADE en logs:")
        for row in cascades:
            print(f"   - {row[0]}: DELETE {row[1]}")
        print(f"   {'✅ Configurado correctamente' if len(cascades) >= 3 else '⚠️  Incompleto'}\n")

        print("=== VERIFICACIÓN COMPLETADA ===\n")

asyncio.run(verify())
