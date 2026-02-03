#!/usr/bin/env python3
"""
Check migration status
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# Check columns
cursor.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'tasks'
    AND column_name IN ('due_date', 'recurring_pattern', 'recurring_interval',
                       'recurring_days', 'recurring_end_date', 'parent_task_id',
                       'next_occurrence')
    ORDER BY column_name;
""")
columns = [row[0] for row in cursor.fetchall()]
print(f"Existing columns in 'tasks': {columns}")

# Check reminders table
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'reminders'
    );
""")
reminders_exists = cursor.fetchone()[0]
print(f"Reminders table exists: {reminders_exists}")

# Check indexes
cursor.execute("""
    SELECT indexname
    FROM pg_indexes
    WHERE tablename IN ('tasks', 'reminders')
    AND indexname LIKE 'idx_%'
    ORDER BY indexname;
""")
indexes = [row[0] for row in cursor.fetchall()]
print(f"Existing indexes: {indexes}")

cursor.close()
conn.close()
