"""Script para verificar la migración de slot_assignments a cages."""
import asyncio
from sqlalchemy import text
from infrastructure.persistence.database import engine


async def verify_migration():
    """Verifica que la migración se aplicó correctamente."""
    async with engine.connect() as conn:
        print("\n=== VERIFICACIÓN POST-MIGRACIÓN ===\n")

        # 1. Verificar que tabla slot_assignments ya no existe
        result = await conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'slot_assignments')"
        ))
        slot_assignments_exists = result.scalar()
        print(f"1. Tabla slot_assignments existe: {slot_assignments_exists}")
        if not slot_assignments_exists:
            print("   ✅ Tabla slot_assignments eliminada correctamente\n")
        else:
            print("   ❌ ERROR: Tabla slot_assignments aún existe\n")

        # 2. Verificar que tabla cages tiene las nuevas columnas
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'cages' AND column_name IN ('line_id', 'slot_number')
            ORDER BY column_name
        """))
        columns = result.fetchall()
        print("2. Columnas nuevas en tabla cages:")
        for col in columns:
            print(f"   - {col[0]} ({col[1]}, nullable={col[2]})")
        if len(columns) == 2:
            print("   ✅ Columnas line_id y slot_number creadas correctamente\n")
        else:
            print(f"   ❌ ERROR: Solo se encontraron {len(columns)} columnas\n")

        # 3. Contar cages con line_id asignado
        result = await conn.execute(text("SELECT COUNT(*) FROM cages WHERE line_id IS NOT NULL"))
        cages_with_line = result.scalar()
        print(f"3. Cages con line_id asignado: {cages_with_line}")

        # 4. Contar total de cages
        result = await conn.execute(text("SELECT COUNT(*) FROM cages"))
        total_cages = result.scalar()
        print(f"   Total de cages: {total_cages}")
        if cages_with_line > 0:
            print(f"   ✅ Datos migrados: {cages_with_line}/{total_cages} cages tienen línea asignada\n")
        else:
            print("   ⚠️  Ninguna cage tiene line_id (puede ser normal si no había slot_assignments)\n")

        # 5. Verificar índice en line_id
        result = await conn.execute(text("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'cages' AND indexname = 'ix_cages_line_id'
        """))
        index_exists = result.fetchone() is not None
        print(f"4. Índice ix_cages_line_id existe: {index_exists}")
        if index_exists:
            print("   ✅ Índice creado correctamente\n")
        else:
            print("   ❌ ERROR: Índice no encontrado\n")

        # 6. Verificar FK de cages.line_id
        result = await conn.execute(text("""
            SELECT constraint_name, delete_rule
            FROM information_schema.referential_constraints
            WHERE constraint_name LIKE '%cages%line_id%'
        """))
        fk = result.fetchone()
        if fk:
            print(f"5. FK cages.line_id: {fk[0]}")
            print(f"   Delete rule: {fk[1]}")
            if fk[1] == 'SET NULL':
                print("   ✅ FK configurada correctamente con SET NULL\n")
            else:
                print(f"   ⚠️  Delete rule es {fk[1]}, esperaba SET NULL\n")
        else:
            print("5. FK cages.line_id: No encontrada")
            print("   ❌ ERROR: FK no encontrada\n")

        # 7. Verificar CASCADE en logs
        result = await conn.execute(text("""
            SELECT tc.table_name, rc.constraint_name, rc.delete_rule
            FROM information_schema.referential_constraints rc
            JOIN information_schema.table_constraints tc
                ON rc.constraint_name = tc.constraint_name
            WHERE tc.table_name IN ('cage_biometry_log', 'cage_mortality_log', 'cage_config_changes_log')
                AND rc.delete_rule = 'CASCADE'
            ORDER BY tc.table_name
        """))
        cascade_fks = result.fetchall()
        print("6. FKs con CASCADE en logs:")
        for fk in cascade_fks:
            print(f"   - {fk[0]}: {fk[1]} (DELETE {fk[2]})")
        if len(cascade_fks) >= 3:
            print("   ✅ CASCADE configurado correctamente en logs\n")
        else:
            print(f"   ⚠️  Solo {len(cascade_fks)} FKs con CASCADE encontradas\n")

        print("=== VERIFICACIÓN COMPLETADA ===\n")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(verify_migration())
