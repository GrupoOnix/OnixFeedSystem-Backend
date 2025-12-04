import asyncio
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text

# Cargar .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

from infrastructure.persistence.database import async_engine

async def verify():
    async with async_engine.begin() as conn:
        print("\n=== VERIFICACION POST-MIGRACION ===\n")

        # 1. Tabla slot_assignments eliminada
        result = await conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'slot_assignments')"
        ))
        print(f"1. Tabla slot_assignments existe: {result.scalar()}")

        # 2. Columnas nuevas
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'cages' AND column_name IN ('line_id', 'slot_number')
        """))
        cols = [r[0] for r in result.fetchall()]
        print(f"2. Columnas nuevas en cages: {cols}")

        # 3. Datos migrados
        result = await conn.execute(text("SELECT COUNT(*) FROM cages WHERE line_id IS NOT NULL"))
        with_line = result.scalar()
        result = await conn.execute(text("SELECT COUNT(*) FROM cages"))
        total = result.scalar()
        print(f"3. Cages con line_id: {with_line}/{total}")

        # 4. Indice
        result = await conn.execute(text(
            "SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'cages' AND indexname = 'ix_cages_line_id'"
        ))
        print(f"4. Indice ix_cages_line_id existe: {result.scalar() > 0}")

        print("\n=== VERIFICACION COMPLETADA ===\n")

asyncio.run(verify())
