"""Script para verificar que las tablas de la Fase 2 se crearon correctamente."""
import asyncio
from sqlalchemy import text
from infrastructure.persistence.database import engine


async def verify_tables():
    """Verifica que las tablas feeding_operations y operation_events existan."""
    async with engine.begin() as conn:
        # Verificar feeding_operations
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'feeding_operations'
            ORDER BY ordinal_position
        """))
        
        print("✅ Tabla feeding_operations:")
        for row in result:
            print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
        
        # Verificar operation_events
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'operation_events'
            ORDER BY ordinal_position
        """))
        
        print("\n✅ Tabla operation_events:")
        for row in result:
            print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
        
        # Verificar FKs
        result = await conn.execute(text("""
            SELECT
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name IN ('feeding_operations', 'operation_events')
        """))
        
        print("\n✅ Foreign Keys:")
        for row in result:
            print(f"  - {row[1]}.{row[2]} → {row[3]}.{row[4]}")
        
        # Verificar que applied_strategy_config fue eliminado
        result = await conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'feeding_sessions'
                AND column_name = 'applied_strategy_config'
        """))
        
        if result.rowcount == 0:
            print("\n✅ Campo 'applied_strategy_config' eliminado de feeding_sessions")
        else:
            print("\n❌ Campo 'applied_strategy_config' todavía existe en feeding_sessions")


if __name__ == "__main__":
    asyncio.run(verify_tables())
