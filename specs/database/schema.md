# Database Schema Specification: Full-Stack Todo Application

## Overview

This document defines the complete database schema for the Full-Stack Todo Application using Neon Serverless PostgreSQL. The schema is designed for user data isolation, performance, and scalability.

**Database:** PostgreSQL 15+ (Neon Serverless)
**ORM:** SQLModel (Python backend)
**Migration Tool:** Alembic
**Last Updated:** 2025-12-12

---

## Schema Design Principles

### 1. User Data Isolation
- All user-owned data includes `user_id` foreign key
- Row-level security policies enforce data access
- Database queries always filter by `user_id`

### 2. Performance Optimization
- Strategic indexes on frequently queried columns
- Composite indexes for common filter combinations
- Timestamps for audit trails and sorting

### 3. Data Integrity
- Foreign key constraints maintain referential integrity
- NOT NULL constraints prevent incomplete data
- Check constraints enforce business rules
- Cascading deletes for data cleanup

### 4. Scalability
- UUID primary keys for distributed systems
- Indexed columns for fast lookups
- Normalized structure prevents data duplication

---

## Tables

### 1. users

**Purpose:** Stores user account information managed by Better Auth.

**Note:** This table is automatically managed by Better Auth. Do not manually modify its structure.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    email_verified BOOLEAN DEFAULT FALSE,
    name VARCHAR(255),
    image TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

#### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique user identifier |
| email | VARCHAR(255) | NOT NULL, UNIQUE | User's email address (login credential) |
| email_verified | BOOLEAN | DEFAULT FALSE | Whether email has been verified |
| name | VARCHAR(255) | NULLABLE | User's display name |
| image | TEXT | NULLABLE | URL to user's profile image |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Account creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last account update timestamp |

#### Indexes

```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
```

#### Business Rules

- Email must be unique across all users
- Email verification status tracked for security
- Timestamps automatically updated on changes

#### Sample Data

```sql
-- Example user record
INSERT INTO users (id, email, email_verified, name, created_at, updated_at)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'john.doe@example.com',
    TRUE,
    'John Doe',
    '2025-12-01T10:00:00Z',
    '2025-12-01T10:00:00Z'
);
```

---

### 2. tasks

**Purpose:** Stores individual todo tasks owned by users.

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title VARCHAR(200) NOT NULL,
    description VARCHAR(1000),
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_tasks_user_id
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT chk_title_not_empty
        CHECK (LENGTH(TRIM(title)) > 0)
);
```

#### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique task identifier |
| user_id | UUID | NOT NULL, FOREIGN KEY → users(id) | Owner of this task |
| title | VARCHAR(200) | NOT NULL, CHECK (LENGTH(TRIM(title)) > 0) | Task title/summary |
| description | VARCHAR(1000) | NULLABLE | Optional detailed description |
| completed | BOOLEAN | NOT NULL, DEFAULT FALSE | Completion status |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Task creation timestamp |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last update timestamp |

#### Indexes

```sql
-- Primary access pattern: Get all tasks for a user
CREATE INDEX idx_tasks_user_id ON tasks(user_id);

-- Common filter: Get incomplete/complete tasks for a user
CREATE INDEX idx_tasks_user_completed ON tasks(user_id, completed);

-- Sorting pattern: Get tasks ordered by creation date
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);

-- Sorting pattern: Get tasks ordered by update date
CREATE INDEX idx_tasks_updated_at ON tasks(updated_at DESC);

-- Composite index for filtered + sorted queries
CREATE INDEX idx_tasks_user_completed_created
    ON tasks(user_id, completed, created_at DESC);
```

#### Foreign Keys

```sql
-- Cascade delete: When user is deleted, all their tasks are deleted
-- Cascade update: If user_id changes (rare), update all task references
CONSTRAINT fk_tasks_user_id
    FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
```

#### Check Constraints

```sql
-- Ensure title is not empty or whitespace-only
CONSTRAINT chk_title_not_empty
    CHECK (LENGTH(TRIM(title)) > 0)
```

#### Business Rules

1. **User Ownership:** Every task MUST belong to a user
2. **Title Required:** Task title cannot be empty or whitespace-only
3. **Description Optional:** Tasks can exist without descriptions
4. **Default Incomplete:** New tasks are created as incomplete
5. **Cascade Deletion:** Deleting a user deletes all their tasks
6. **Timestamp Tracking:** Creation and update times automatically maintained

#### Sample Data

```sql
-- Example task records
INSERT INTO tasks (id, user_id, title, description, completed, created_at, updated_at)
VALUES
(
    '660e8400-e29b-41d4-a716-446655440001',
    '550e8400-e29b-41d4-a716-446655440000',
    'Complete project documentation',
    'Write comprehensive API documentation for the todo app',
    FALSE,
    '2025-12-10T14:30:00Z',
    '2025-12-10T14:30:00Z'
),
(
    '660e8400-e29b-41d4-a716-446655440002',
    '550e8400-e29b-41d4-a716-446655440000',
    'Review pull requests',
    NULL,
    TRUE,
    '2025-12-09T09:15:00Z',
    '2025-12-11T16:45:00Z'
),
(
    '660e8400-e29b-41d4-a716-446655440003',
    '550e8400-e29b-41d4-a716-446655440000',
    'Deploy to production',
    'Deploy the todo app to Vercel and Render',
    FALSE,
    '2025-12-12T10:05:00Z',
    '2025-12-12T10:05:00Z'
);
```

---

## Entity Relationships

### ER Diagram (Mermaid)

```mermaid
erDiagram
    users ||--o{ tasks : owns

    users {
        UUID id PK
        VARCHAR email UK
        BOOLEAN email_verified
        VARCHAR name
        TEXT image
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    tasks {
        UUID id PK
        UUID user_id FK
        VARCHAR title
        VARCHAR description
        BOOLEAN completed
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }
```

### Relationship Details

#### users → tasks (One-to-Many)

**Relationship:** One user can have many tasks
**Cardinality:** 1:N (one-to-many)
**Foreign Key:** `tasks.user_id` → `users.id`
**Delete Behavior:** CASCADE (deleting user deletes all their tasks)
**Update Behavior:** CASCADE (updating user.id updates all task references)

**Business Logic:**
- A user can have 0 to unlimited tasks
- A task MUST belong to exactly one user
- Users cannot see or modify tasks belonging to other users

---

## SQLModel Definitions

### User Model (Managed by Better Auth)

```python
from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(max_length=255, unique=True, index=True)
    email_verified: bool = Field(default=False)
    name: Optional[str] = Field(default=None, max_length=255)
    image: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Task Model

```python
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=200, min_length=1)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Validation
    @property
    def validate_title(self) -> bool:
        """Ensure title is not empty or whitespace-only."""
        return len(self.title.strip()) > 0
```

---

## Migration Scripts

### Initial Migration (Alembic)

```python
"""Initial schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-12-12 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create users table (managed by Better Auth)
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.VARCHAR(255), nullable=False, unique=True),
        sa.Column('email_verified', sa.BOOLEAN(), nullable=False,
                  server_default=sa.text('FALSE')),
        sa.Column('name', sa.VARCHAR(255), nullable=True),
        sa.Column('image', sa.TEXT(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('NOW()'))
    )

    # Create indexes on users
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.VARCHAR(200), nullable=False),
        sa.Column('description', sa.VARCHAR(1000), nullable=True),
        sa.Column('completed', sa.BOOLEAN(), nullable=False,
                  server_default=sa.text('FALSE')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'],
                                name='fk_tasks_user_id',
                                ondelete='CASCADE',
                                onupdate='CASCADE'),
        sa.CheckConstraint("LENGTH(TRIM(title)) > 0",
                           name='chk_title_not_empty')
    )

    # Create indexes on tasks
    op.create_index('idx_tasks_user_id', 'tasks', ['user_id'])
    op.create_index('idx_tasks_user_completed', 'tasks',
                    ['user_id', 'completed'])
    op.create_index('idx_tasks_created_at', 'tasks', ['created_at'],
                    postgresql_ops={'created_at': 'DESC'})
    op.create_index('idx_tasks_updated_at', 'tasks', ['updated_at'],
                    postgresql_ops={'updated_at': 'DESC'})
    op.create_index('idx_tasks_user_completed_created', 'tasks',
                    ['user_id', 'completed', 'created_at'],
                    postgresql_ops={'created_at': 'DESC'})

def downgrade() -> None:
    op.drop_table('tasks')
    op.drop_table('users')
```

---

## Query Patterns

### Common Queries with Index Usage

#### 1. Get All Tasks for User (Sorted by Creation Date)

```sql
-- Uses: idx_tasks_user_id or idx_tasks_user_completed_created
SELECT * FROM tasks
WHERE user_id = '550e8400-e29b-41d4-a716-446655440000'
ORDER BY created_at DESC;
```

**Index Used:** `idx_tasks_user_id` + sort on `idx_tasks_created_at`
**Performance:** O(log n) lookup + sequential scan of user's tasks

#### 2. Get Incomplete Tasks for User

```sql
-- Uses: idx_tasks_user_completed
SELECT * FROM tasks
WHERE user_id = '550e8400-e29b-41d4-a716-446655440000'
  AND completed = FALSE
ORDER BY created_at DESC;
```

**Index Used:** `idx_tasks_user_completed` (composite index covers both filters)
**Performance:** O(log n) lookup, optimal for filtered queries

#### 3. Create New Task

```sql
-- Auto-generates id, sets defaults for completed, created_at, updated_at
INSERT INTO tasks (user_id, title, description)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'New task title',
    'Optional description'
)
RETURNING *;
```

**Performance:** O(log n) for index updates
**Constraints Checked:** NOT NULL, foreign key, title not empty

#### 4. Update Task

```sql
-- Partial update (only provided fields)
UPDATE tasks
SET
    title = 'Updated title',
    updated_at = NOW()
WHERE id = '660e8400-e29b-41d4-a716-446655440001'
  AND user_id = '550e8400-e29b-41d4-a716-446655440000'
RETURNING *;
```

**Index Used:** Primary key (id) + verification filter (user_id)
**Performance:** O(log n) lookup
**Security:** user_id filter prevents cross-user modification

#### 5. Toggle Task Completion

```sql
-- Toggle completed status
UPDATE tasks
SET
    completed = NOT completed,
    updated_at = NOW()
WHERE id = '660e8400-e29b-41d4-a716-446655440001'
  AND user_id = '550e8400-e29b-41d4-a716-446655440000'
RETURNING *;
```

**Index Used:** Primary key (id)
**Performance:** O(log n) lookup
**Business Logic:** NOT operator toggles boolean

#### 6. Delete Task

```sql
-- Permanent deletion
DELETE FROM tasks
WHERE id = '660e8400-e29b-41d4-a716-446655440001'
  AND user_id = '550e8400-e29b-41d4-a716-446655440000'
RETURNING id;
```

**Index Used:** Primary key (id)
**Performance:** O(log n) lookup
**Security:** user_id filter prevents cross-user deletion

#### 7. Get Task Count by Status

```sql
-- Aggregate query for dashboard metrics
SELECT
    completed,
    COUNT(*) as count
FROM tasks
WHERE user_id = '550e8400-e29b-41d4-a716-446655440000'
GROUP BY completed;
```

**Index Used:** `idx_tasks_user_completed`
**Performance:** O(log n) + O(m) where m = user's task count
**Output:** `[{completed: false, count: 5}, {completed: true, count: 3}]`

---

## Performance Considerations

### Index Strategy

**Primary Indexes:**
1. `idx_tasks_user_id` - Fast user-specific lookups
2. `idx_tasks_user_completed` - Filtered queries (show incomplete tasks)
3. `idx_tasks_created_at` - Sorting by creation date
4. `idx_tasks_user_completed_created` - Composite for filtered + sorted queries

**Index Size Estimates:**
- UUID index: ~16 bytes per row
- Boolean index: ~1 byte per row
- Timestamp index: ~8 bytes per row
- For 1M tasks: ~25MB total index size

### Query Performance Targets

| Query Type | Target Response Time | Scalability |
|------------|---------------------|-------------|
| List tasks (user) | < 100ms | Up to 10,000 tasks/user |
| Get single task | < 30ms | O(log n) |
| Create task | < 50ms | O(log n) |
| Update task | < 50ms | O(log n) |
| Delete task | < 50ms | O(log n) |
| Toggle completion | < 50ms | O(log n) |

### Scalability Limits

**Current Design Supports:**
- 1,000,000+ users
- 100,000,000+ total tasks
- 10,000+ tasks per user
- 100+ concurrent users per second

**Bottleneck Analysis:**
- **Database Connections:** Use connection pooling (20-50 connections)
- **Index Size:** Indexes scale linearly with row count
- **Query Performance:** Logarithmic scaling with proper indexes

---

## Security Measures

### Row-Level Security (RLS)

```sql
-- Enable RLS on tasks table
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own tasks
CREATE POLICY tasks_isolation_policy ON tasks
    FOR ALL
    TO authenticated_user
    USING (user_id = current_user_id());

-- Policy: Users can only insert tasks for themselves
CREATE POLICY tasks_insert_policy ON tasks
    FOR INSERT
    TO authenticated_user
    WITH CHECK (user_id = current_user_id());
```

### Application-Level Security

**Required Checks:**
1. **Authentication:** Verify JWT token on all requests
2. **Authorization:** Extract `user_id` from token
3. **Query Filtering:** Always include `WHERE user_id = ?` in queries
4. **Prevent SQL Injection:** Use parameterized queries (SQLModel handles this)

**Example Secure Query (SQLModel):**
```python
from sqlmodel import select

# SECURE: Parameterized query prevents SQL injection
stmt = select(Task).where(
    Task.user_id == current_user_id,
    Task.id == task_id
)
task = session.exec(stmt).first()
```

---

## Data Retention & Cleanup

### Automatic Cleanup

**Cascade Deletions:**
- Deleting a user automatically deletes all their tasks
- Implemented via `ON DELETE CASCADE` foreign key constraint

### Manual Cleanup (Future)

**Soft Deletes (Optional Enhancement):**
```sql
-- Add deleted_at column for soft deletes
ALTER TABLE tasks ADD COLUMN deleted_at TIMESTAMP WITH TIME ZONE;

-- Mark as deleted instead of hard delete
UPDATE tasks
SET deleted_at = NOW()
WHERE id = ?;

-- Query only active tasks
SELECT * FROM tasks
WHERE user_id = ? AND deleted_at IS NULL;
```

**Archive Old Completed Tasks:**
```sql
-- Move tasks completed > 90 days ago to archive table
INSERT INTO tasks_archive
SELECT * FROM tasks
WHERE completed = TRUE
  AND updated_at < NOW() - INTERVAL '90 days';

DELETE FROM tasks
WHERE completed = TRUE
  AND updated_at < NOW() - INTERVAL '90 days';
```

---

## Backup & Recovery

### Neon Serverless Features

**Automatic Backups:**
- Point-in-time recovery (PITR) up to 7 days
- Automatic snapshots every 24 hours
- Retained for 7 days (configurable)

**Disaster Recovery:**
```sql
-- Restore database to specific timestamp
-- (Performed via Neon Console or API)
RESTORE DATABASE todo_app
TO TIMESTAMP '2025-12-12T10:00:00Z';
```

### Manual Backups

```bash
# Export full database
pg_dump -h neon-host.neon.tech \
        -U neon_user \
        -d todo_app \
        -F c -f backup_$(date +%Y%m%d).dump

# Restore from backup
pg_restore -h neon-host.neon.tech \
           -U neon_user \
           -d todo_app \
           backup_20251212.dump
```

---

## Testing Data

### Seed Data Script

```sql
-- Create test user
INSERT INTO users (id, email, email_verified, name)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'test@example.com',
    TRUE,
    'Test User'
);

-- Create test tasks
INSERT INTO tasks (user_id, title, description, completed) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'Buy groceries', 'Milk, eggs, bread', FALSE),
('550e8400-e29b-41d4-a716-446655440000', 'Finish homework', NULL, FALSE),
('550e8400-e29b-41d4-a716-446655440000', 'Call dentist', 'Schedule cleaning', FALSE),
('550e8400-e29b-41d4-a716-446655440000', 'Read book', 'Chapter 5-7', TRUE),
('550e8400-e29b-41d4-a716-446655440000', 'Exercise', '30 min cardio', TRUE);
```

### Cleanup Test Data

```sql
-- Delete all test data
DELETE FROM tasks WHERE user_id = '550e8400-e29b-41d4-a716-446655440000';
DELETE FROM users WHERE email = 'test@example.com';
```

---

## Monitoring & Maintenance

### Health Checks

```sql
-- Check table row counts
SELECT
    'users' as table_name,
    COUNT(*) as row_count
FROM users
UNION ALL
SELECT
    'tasks' as table_name,
    COUNT(*) as row_count
FROM tasks;

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Check table sizes
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Performance Monitoring

```sql
-- Slow queries (requires pg_stat_statements extension)
SELECT
    query,
    calls,
    mean_exec_time,
    max_exec_time,
    stddev_exec_time
FROM pg_stat_statements
WHERE query LIKE '%tasks%'
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Lock monitoring
SELECT
    t.relname,
    l.locktype,
    l.mode,
    l.granted
FROM pg_locks l
JOIN pg_stat_all_tables t ON l.relation = t.relid
WHERE t.schemaname = 'public';
```

---

## Changelog

### Version 1.0.0 (2025-12-12)

**Initial Schema:**
- `users` table (Better Auth managed)
- `tasks` table with full CRUD support
- Composite indexes for performance
- Foreign key constraints with cascade
- Check constraints for data validation
- Row-level security policies

---

## Future Enhancements

### Planned Additions

**Phase 3: AI Chatbot**
- Add `conversations` table
- Add `messages` table
- Link messages to tasks

**Phase 4: Kubernetes**
- Connection pooling optimization
- Read replicas for scaling
- Sharding strategy for 10M+ users

**Phase 5: Event-Driven**
- Add `events` table for Kafka integration
- Event sourcing for task history
- CQRS pattern implementation

---

## Appendix

### A. SQL Naming Conventions

- **Tables:** Lowercase, plural nouns (`users`, `tasks`)
- **Columns:** Lowercase, snake_case (`user_id`, `created_at`)
- **Indexes:** Prefix with `idx_`, descriptive name (`idx_tasks_user_id`)
- **Constraints:** Prefix with type (`fk_`, `chk_`, `pk_`, `uk_`)

### B. PostgreSQL Extensions

**Required Extensions:**
```sql
-- UUID generation (built-in PostgreSQL 13+)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Performance monitoring
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
```

### C. Environment Variables

```env
# Neon Database Connection
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require

# Connection Pool Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
```

---

**Last Updated:** 2025-12-12
**Schema Version:** 1.0.0
**Maintained By:** Development Team
