#!/usr/bin/env python3
"""
Finish migration 003 - Create reminders table and indexes
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv('DATABASE_URL')

# SQL for remaining migration steps
create_reminders_table = """
CREATE TABLE IF NOT EXISTS reminders (
  id SERIAL PRIMARY KEY,
  task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  user_id VARCHAR(255) NOT NULL,
  remind_at TIMESTAMPTZ NOT NULL,
  delivered BOOLEAN DEFAULT FALSE,
  delivery_status VARCHAR(20) DEFAULT 'pending' CHECK (delivery_status IN ('pending', 'sent', 'failed', 'dismissed')),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
"""

# Indexes for tasks table (CONCURRENT)
task_indexes = [
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_due_date ON tasks(due_date) WHERE due_date IS NOT NULL",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_parent_task_id ON tasks(parent_task_id) WHERE parent_task_id IS NOT NULL",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_recurring_pattern ON tasks(recurring_pattern) WHERE recurring_pattern != 'none'",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_next_occurrence ON tasks(next_occurrence) WHERE next_occurrence IS NOT NULL"
]

# Indexes for reminders table (CONCURRENT)
reminder_indexes = [
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reminders_task_id ON reminders(task_id)",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reminders_user_id ON reminders(user_id)",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reminders_remind_at ON reminders(remind_at) WHERE delivered = FALSE"
]

# Comments
comments = """
COMMENT ON TABLE reminders IS 'Stores scheduled reminders for tasks with due dates';
COMMENT ON COLUMN tasks.due_date IS 'Task due date with timezone';
COMMENT ON COLUMN tasks.recurring_pattern IS 'Recurrence pattern: none, daily, weekly, monthly, custom';
COMMENT ON COLUMN tasks.recurring_interval IS 'Interval for recurrence (e.g., every 2 weeks)';
COMMENT ON COLUMN tasks.recurring_days IS 'Days of week for weekly recurrence (e.g., {Mon,Wed,Fri})';
COMMENT ON COLUMN tasks.recurring_end_date IS 'End date for recurring series';
COMMENT ON COLUMN tasks.parent_task_id IS 'Reference to parent task for recurring instances';
COMMENT ON COLUMN tasks.next_occurrence IS 'Cached next occurrence timestamp for recurring tasks';
"""

try:
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()

    # Step 1: Create reminders table (in transaction)
    print("Step 1: Creating reminders table...")
    cursor.execute(create_reminders_table)
    for comment in comments.strip().split(';'):
        if comment.strip():
            cursor.execute(comment.strip() + ';')
    conn.commit()
    print("  Reminders table created")

    # Step 2: Create indexes (with autocommit for CONCURRENT)
    print("Step 2: Creating indexes...")
    conn.set_session(autocommit=True)

    for idx_sql in task_indexes + reminder_indexes:
        idx_name = idx_sql.split()[5]  # Extract index name
        print(f"  Creating {idx_name}...")
        cursor.execute(idx_sql)

    print("\nSUCCESS: Migration completed!")

    # Verify
    cursor.execute("""
        SELECT indexname
        FROM pg_indexes
        WHERE tablename IN ('tasks', 'reminders')
        AND indexname LIKE 'idx_%'
        ORDER BY indexname;
    """)
    indexes = [row[0] for row in cursor.fetchall()]
    print(f"\nCreated indexes:")
    for idx in indexes:
        print(f"  - {idx}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
