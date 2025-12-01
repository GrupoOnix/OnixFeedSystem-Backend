"""
Script to fix feeding_sessions and feeding_events tables to match the updated migration.
This adds missing indexes and foreign key constraints.
"""
import asyncio
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables
load_dotenv()

from src.infrastructure.persistence.database import async_engine


async def fix_tables():
    """Add missing indexes and constraints to feeding tables."""
    engine = async_engine
    
    async with engine.begin() as conn:
        print("Adding missing indexes and constraints...")
        
        # Add missing indexes to feeding_sessions
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_feeding_sessions_date ON feeding_sessions (date)"
            ))
            print("✓ Added index on feeding_sessions.date")
        except Exception as e:
            print(f"✗ Error adding date index: {e}")
        
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_feeding_sessions_status ON feeding_sessions (status)"
            ))
            print("✓ Added index on feeding_sessions.status")
        except Exception as e:
            print(f"✗ Error adding status index: {e}")
        
        # Add missing index to feeding_events
        try:
            await conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_feeding_events_timestamp ON feeding_events (timestamp)"
            ))
            print("✓ Added index on feeding_events.timestamp")
        except Exception as e:
            print(f"✗ Error adding timestamp index: {e}")
        
        # Add foreign key constraint to feeding_sessions.line_id
        try:
            # First check if constraint already exists
            result = await conn.execute(text("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'feeding_sessions' 
                AND constraint_type = 'FOREIGN KEY'
                AND constraint_name LIKE '%line_id%'
            """))
            existing = result.fetchone()
            
            if not existing:
                await conn.execute(text(
                    "ALTER TABLE feeding_sessions ADD CONSTRAINT feeding_sessions_line_id_fkey "
                    "FOREIGN KEY (line_id) REFERENCES feeding_lines(id)"
                ))
                print("✓ Added foreign key constraint on feeding_sessions.line_id")
            else:
                print("✓ Foreign key constraint on feeding_sessions.line_id already exists")
        except Exception as e:
            print(f"✗ Error adding line_id foreign key: {e}")
        
        # Update feeding_events foreign key to include CASCADE
        try:
            # Check current constraint
            result = await conn.execute(text("""
                SELECT tc.constraint_name, rc.delete_rule
                FROM information_schema.table_constraints tc
                JOIN information_schema.referential_constraints rc 
                ON tc.constraint_name = rc.constraint_name
                WHERE tc.table_name = 'feeding_events'
                AND tc.constraint_type = 'FOREIGN KEY'
            """))
            constraint = result.fetchone()
            
            if constraint:
                constraint_name = constraint[0]
                delete_rule = constraint[1]
                
                if delete_rule != 'CASCADE':
                    # Drop old constraint and recreate with CASCADE
                    await conn.execute(text(
                        f"ALTER TABLE feeding_events DROP CONSTRAINT {constraint_name}"
                    ))
                    await conn.execute(text(
                        "ALTER TABLE feeding_events ADD CONSTRAINT feeding_events_session_id_fkey "
                        "FOREIGN KEY (session_id) REFERENCES feeding_sessions(id) ON DELETE CASCADE"
                    ))
                    print("✓ Updated foreign key constraint on feeding_events.session_id to CASCADE")
                else:
                    print("✓ Foreign key constraint on feeding_events.session_id already has CASCADE")
            else:
                # No constraint exists, add it
                await conn.execute(text(
                    "ALTER TABLE feeding_events ADD CONSTRAINT feeding_events_session_id_fkey "
                    "FOREIGN KEY (session_id) REFERENCES feeding_sessions(id) ON DELETE CASCADE"
                ))
                print("✓ Added foreign key constraint on feeding_events.session_id with CASCADE")
        except Exception as e:
            print(f"✗ Error updating session_id foreign key: {e}")
        
        print("\nDatabase schema updated successfully!")


if __name__ == "__main__":
    asyncio.run(fix_tables())
