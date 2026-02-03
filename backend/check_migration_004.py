#!/usr/bin/env python3
"""
Check migration 004 status - Kafka event schema
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# Check audit_logs table
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'audit_logs'
    );
""")
audit_logs_exists = cursor.fetchone()[0]
print(f"audit_logs table exists: {audit_logs_exists}")

# Check notification_subscriptions table
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'notification_subscriptions'
    );
""")
notification_subs_exists = cursor.fetchone()[0]
print(f"notification_subscriptions table exists: {notification_subs_exists}")

# Check idempotency index on tasks
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM pg_indexes
        WHERE tablename = 'tasks'
        AND indexname = 'idx_recurring_instance_dedup'
    );
""")
dedup_index_exists = cursor.fetchone()[0]
print(f"idx_recurring_instance_dedup index exists: {dedup_index_exists}")

if audit_logs_exists:
    # Check audit_logs columns
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'audit_logs'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    print(f"\naudit_logs columns: {len(columns)}")
    for col, dtype in columns:
        print(f"  - {col}: {dtype}")

if notification_subs_exists:
    # Check notification_subscriptions columns
    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'notification_subscriptions'
        ORDER BY ordinal_position;
    """)
    columns = cursor.fetchall()
    print(f"\nnotification_subscriptions columns: {len(columns)}")
    for col, dtype in columns:
        print(f"  - {col}: {dtype}")

cursor.close()
conn.close()

# Summary
print("\n=== Migration 004 Status ===")
if audit_logs_exists and notification_subs_exists and dedup_index_exists:
    print("✓ Migration 004 is APPLIED")
else:
    print("✗ Migration 004 is NOT APPLIED")
    print("\nRun: python apply_migration.py 004")
