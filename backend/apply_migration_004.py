#!/usr/bin/env python3
"""
Script to apply database migration 004 - Kafka event schema
"""
import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_migration_004():
    """Apply migration 004 to the database"""
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print("ERROR: DATABASE_URL not found in environment")
        return False

    migration_file = 'migrations/004_add_kafka_event_schema.sql'

    if not os.path.exists(migration_file):
        print(f"ERROR: Migration file not found: {migration_file}")
        return False

    try:
        # Read migration SQL
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # Connect to database
        print(f"Connecting to database...")
        conn = psycopg2.connect(database_url)
        conn.autocommit = True  # Required for CREATE INDEX CONCURRENTLY
        cursor = conn.cursor()

        print(f"Applying migration: {migration_file}")

        # Execute the entire migration (it's wrapped in BEGIN/COMMIT)
        cursor.execute(migration_sql)

        print("SUCCESS: Migration 004 applied successfully!")

        # Verify tables exist
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('audit_logs', 'notification_subscriptions')
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"\nCreated tables: {tables}")

        # Verify indexes
        cursor.execute("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'audit_logs'
            OR (tablename = 'tasks' AND indexname = 'idx_recurring_instance_dedup')
            ORDER BY indexname;
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        print(f"Created indexes: {len(indexes)} indexes")

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        print(f"ERROR: Database error: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == '__main__':
    success = apply_migration_004()
    exit(0 if success else 1)
