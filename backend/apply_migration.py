#!/usr/bin/env python3
"""
Script to apply database migration 003
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_migration():
    """Apply migration 003 to the database"""
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return False

    migration_file = 'migrations/003_add_due_dates_reminders.sql'

    if not os.path.exists(migration_file):
        print(f"ERROR: Migration file not found: {migration_file}")
        return False

    try:
        # Read migration SQL
        with open(migration_file, 'r') as f:
            migration_sql = f.read()

        # Split into regular SQL and CONCURRENT index SQL
        statements = []
        concurrent_statements = []

        for stmt in migration_sql.split(';'):
            stmt = stmt.strip()
            if stmt:
                if 'CONCURRENTLY' in stmt.upper():
                    concurrent_statements.append(stmt + ';')
                else:
                    statements.append(stmt + ';')

        # Connect and apply regular statements in transaction
        print(f"Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print(f"Applying migration: {migration_file}")
        print(f"  Step 1: Regular statements (in transaction)")
        for stmt in statements:
            if stmt.strip():
                cursor.execute(stmt)
        conn.commit()

        # Apply CONCURRENT indexes with autocommit
        if concurrent_statements:
            print(f"  Step 2: CONCURRENT indexes (autocommit)")
            conn.set_session(autocommit=True)
            for stmt in concurrent_statements:
                if stmt.strip():
                    cursor.execute(stmt)

        print("SUCCESS: Migration applied successfully!")

        # Verify tables exist
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('tasks', 'reminders')
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f"\nVerified tables: {[t[0] for t in tables]}")

        # Verify new columns in tasks table
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'tasks'
            AND column_name IN ('due_date', 'recurring_pattern', 'recurring_interval',
                               'recurring_days', 'recurring_end_date', 'parent_task_id',
                               'next_occurrence')
            ORDER BY column_name;
        """)
        columns = cursor.fetchall()
        print(f"\nNew columns in 'tasks' table:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")

        # Verify indexes
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename IN ('tasks', 'reminders')
            AND indexname LIKE 'idx_%'
            ORDER BY indexname;
        """)
        indexes = cursor.fetchall()
        print(f"\nCreated indexes:")
        for idx in indexes:
            print(f"  - {idx[0]}")

        cursor.close()
        conn.close()

        return True

    except psycopg2.Error as e:
        print(f"ERROR: Database error: {e}")
        if 'conn' in locals():
            try:
                conn.rollback()
            except:
                pass
            conn.close()
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == '__main__':
    success = apply_migration()
    exit(0 if success else 1)
