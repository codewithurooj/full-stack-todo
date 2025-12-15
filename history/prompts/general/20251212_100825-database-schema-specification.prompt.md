---
id: 20251212_100825
title: database-schema-specification
stage: spec
date: 2025-12-12T10:08:25Z
surface: claude-code
model: claude-sonnet-4.5
feature: database-schema
branch: 001-task-crud
user: pc1
command: /sp.specify
labels: [database, schema, postgresql, sqlmodel, neon]
links:
  spec: specs/database/schema.md
  ticket: null
  adr: null
  pr: null
files:
  - path: specs/database/schema.md
    status: created
    lines: 834
tests:
  - name: null
    status: null
---

## Prompt

User requested: "Write database schema in /specs/database/ - schema.md - Table definitions and relationships"

The user wanted comprehensive database schema documentation for the Full-Stack Todo Application using Neon Serverless PostgreSQL, covering:
1. Complete table definitions (users, tasks)
2. Entity relationships and foreign keys
3. Indexes and performance optimization
4. SQLModel definitions for ORM
5. Migration scripts (Alembic)
6. Common query patterns
7. Security measures (RLS policies)
8. Performance considerations
9. Backup and recovery strategies

## Response snapshot

Created a comprehensive database schema specification document at `specs/database/schema.md` with the following sections:

**Structure:**

1. **Overview** - Database technology, ORM, migration tools
2. **Schema Design Principles** - User data isolation, performance, data integrity, scalability
3. **Tables (2 total)**:
   - **users** - Better Auth managed, stores user accounts
     - 7 columns: id (UUID PK), email (unique), email_verified, name, image, created_at, updated_at
     - 2 indexes: email, created_at
   - **tasks** - User-owned todo items
     - 7 columns: id (UUID PK), user_id (FK), title, description, completed, created_at, updated_at
     - 5 indexes: user_id, user+completed, created_at, updated_at, composite
     - 1 foreign key: user_id → users.id (CASCADE)
     - 1 check constraint: title not empty

4. **Entity Relationships** - ER diagram (Mermaid), 1:N users→tasks relationship
5. **SQLModel Definitions** - Python model classes for User and Task
6. **Migration Scripts** - Complete Alembic migration for initial schema
7. **Query Patterns** - 7 common queries with index usage analysis:
   - Get all tasks for user (sorted)
   - Get incomplete tasks
   - Create new task
   - Update task
   - Toggle task completion
   - Delete task
   - Get task count by status

8. **Performance Considerations**:
   - Index strategy and size estimates
   - Query performance targets (< 100ms for list, < 50ms for CRUD)
   - Scalability limits (1M+ users, 100M+ tasks)
   - Bottleneck analysis

9. **Security Measures**:
   - Row-level security (RLS) policies
   - Application-level checks
   - SQL injection prevention
   - Secure query examples

10. **Data Retention & Cleanup** - Cascade deletions, soft delete pattern, archiving strategy
11. **Backup & Recovery** - Neon PITR, manual backup commands
12. **Testing Data** - Seed data script, cleanup script
13. **Monitoring & Maintenance** - Health checks, performance monitoring queries
14. **Changelog** - v1.0.0 initial schema
15. **Future Enhancements** - Phase 3-5 additions (conversations, Kubernetes optimization, event sourcing)
16. **Appendix** - Naming conventions, PostgreSQL extensions, environment variables

**Key Features:**
- Complete schema for 2 tables (users, tasks)
- 7 strategic indexes for optimal performance
- Foreign key with CASCADE for data integrity
- Check constraint for business rules
- SQLModel Python definitions
- Alembic migration script
- 7 common query patterns documented
- Row-level security policies
- Performance targets specified
- Backup/recovery procedures
- Monitoring queries included

**Technical Highlights:**
- UUID primary keys for distributed scalability
- Composite indexes for filtered + sorted queries
- O(log n) query performance via proper indexing
- Supports 1M+ users, 100M+ tasks
- < 100ms response times for all operations
- Cascade delete maintains referential integrity
- RLS policies enforce user data isolation

## Outcome

- ✅ Impact: Created production-ready database schema specification (834 lines) defining complete data model, relationships, indexes, and performance characteristics
- 🧪 Tests: Documented seed data script, cleanup procedures, health checks, and performance monitoring queries
- 📁 Files: Created `specs/database/schema.md`
- 🔁 Next prompts:
  - Implement backend models using SQLModel based on this schema
  - Create Alembic migration files from the migration script
  - Set up Neon database and apply schema
  - Implement RLS policies for production security
- 🧠 Reflection: The schema spec provides a complete database contract with emphasis on performance (strategic indexes), security (RLS policies), and scalability (UUID PKs, composite indexes). The inclusion of query patterns, SQLModel definitions, and migration scripts enables immediate implementation.

## Evaluation notes (flywheel)

- Failure modes observed: None - schema specification created successfully on first attempt
- Graders run and results (PASS/FAIL): N/A (documentation task)
- Prompt variant (if applicable): Used /sp.specify command with database schema focus
- Next experiment (smallest change to try): Use this schema to generate SQLModel classes with fastapi-sqlmodel skill and validate schema completeness
