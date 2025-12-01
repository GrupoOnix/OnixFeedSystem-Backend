"""
Script to verify that feeding_sessions and feeding_events tables have all required elements.
"""
import asyncio
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables
load_dotenv()

from src.infrastructure.persistence.database import async_engine


async def verify_tables():
    """Verify all required indexes and constraints exist."""
    engine = async_engine
    
    async with engine.begin() as conn:
        print("Verifying feeding_sessions table...")
        print("=" * 60)
        
        # Check columns
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'feeding_sessions'
            ORDER BY ordinal_position
        """))
        columns = result.fetchall()
        print("\nColumns:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # Check indexes
        result = await conn.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'feeding_sessions'
            ORDER BY indexname
        """))
        indexes = result.fetchall()
        print("\nIndexes:")
        for idx in indexes:
            print(f"  - {idx[0]}")
        
        # Check foreign keys
        result = await conn.execute(text("""
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            WHERE tc.table_name = 'feeding_sessions'
              AND tc.constraint_type = 'FOREIGN KEY'
        """))
        fkeys = result.fetchall()
        print("\nForeign Keys:")
        for fk in fkeys:
            print(f"  - {fk[0]}: {fk[1]} -> {fk[2]}.{fk[3]}")
        
        print("\n" + "=" * 60)
        print("Verifying feeding_events table...")
        print("=" * 60)
        
        # Check columns
        result = await conn.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'feeding_events'
            ORDER BY ordinal_position
        """))
        columns = result.fetchall()
        print("\nColumns:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        # Check indexes
        result = await conn.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'feeding_events'
            ORDER BY indexname
        """))
        indexes = result.fetchall()
        print("\nIndexes:")
        for idx in indexes:
            print(f"  - {idx[0]}")
        
        # Check foreign keys with CASCADE
        result = await conn.execute(text("""
            SELECT
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
            JOIN information_schema.referential_constraints AS rc
              ON tc.constraint_name = rc.constraint_name
            WHERE tc.table_name = 'feeding_events'
              AND tc.constraint_type = 'FOREIGN KEY'
        """))
        fkeys = result.fetchall()
        print("\nForeign Keys:")
        for fk in fkeys:
            print(f"  - {fk[0]}: {fk[1]} -> {fk[2]}.{fk[3]} (ON DELETE {fk[4]})")
        
        print("\n" + "=" * 60)
        print("Verification Summary:")
        print("=" * 60)
        
        # Verify requirements
        checks = {
            "feeding_sessions has line_id foreign key": False,
            "feeding_sessions has date index": False,
            "feeding_sessions has status index": False,
            "feeding_events has timestamp index": False,
            "feeding_events has CASCADE delete": False,
        }
        
        # Check feeding_sessions foreign key
        result = await conn.execute(text("""
            SELECT COUNT(*)
            FROM information_schema.table_constraints
            WHERE table_name = 'feeding_sessions'
              AND constraint_type = 'FOREIGN KEY'
        """))
        if result.scalar() > 0:
            checks["feeding_sessions has line_id foreign key"] = True
        
        # Check indexes
        result = await conn.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'feeding_sessions'
        """))
        session_indexes = [row[0] for row in result.fetchall()]
        
        if any('date' in idx for idx in session_indexes):
            checks["feeding_sessions has date index"] = True
        if any('status' in idx for idx in session_indexes):
            checks["feeding_sessions has status index"] = True
        
        result = await conn.execute(text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'feeding_events'
        """))
        event_indexes = [row[0] for row in result.fetchall()]
        
        if any('timestamp' in idx for idx in event_indexes):
            checks["feeding_events has timestamp index"] = True
        
        # Check CASCADE
        result = await conn.execute(text("""
            SELECT rc.delete_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.referential_constraints rc
              ON tc.constraint_name = rc.constraint_name
            WHERE tc.table_name = 'feeding_events'
              AND tc.constraint_type = 'FOREIGN KEY'
        """))
        delete_rule = result.scalar()
        if delete_rule == 'CASCADE':
            checks["feeding_events has CASCADE delete"] = True
        
        print()
        for check, passed in checks.items():
            status = "✓" if passed else "✗"
            print(f"{status} {check}")
        
        all_passed = all(checks.values())
        print()
        if all_passed:
            print("✓ All requirements verified successfully!")
        else:
            print("✗ Some requirements are missing")
        
        return all_passed


if __name__ == "__main__":
    result = asyncio.run(verify_tables())
    exit(0 if result else 1)
