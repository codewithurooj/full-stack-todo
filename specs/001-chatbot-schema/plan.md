# Implementation Plan: AI Chatbot Database Schema

**Branch**: `001-chatbot-schema` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-chatbot-schema/spec.md`

## Summary

This feature implements the database schema foundation for Phase III AI-powered chatbot functionality. It adds two new tables (`conversations` and `messages`) to the existing PostgreSQL database to enable stateless chat endpoints that persist conversation history. The implementation uses SQLModel for ORM, Alembic for migrations, and follows Phase II's established patterns for database management.

**Primary Requirement**: Enable persistent storage of chat conversations and messages to support stateless AI chatbot architecture where conversation context is fetched from the database for each request.

**Technical Approach**: Create database migration scripts using Alembic to add new tables with proper foreign key relationships, indexes, and constraints. Use SQLModel to define Python models that map to these tables, ensuring compatibility with the existing Phase II codebase.

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: SQLModel, Alembic, psycopg2-binary, Neon PostgreSQL driver
**Storage**: Neon Serverless PostgreSQL (existing from Phase II)
**Testing**: pytest with pytest-postgresql for database tests
**Target Platform**: Linux server (Render/Railway deployment)
**Project Type**: Web application (backend component)
**Performance Goals**:
- < 100ms for conversation list queries (100 conversations)
- < 50ms for message history queries (50 messages)
- Support concurrent writes without data corruption
**Constraints**:
- Must not break existing task management functionality
- Must maintain stateless API design (no server-side sessions)
- Must work with existing Neon PostgreSQL connection
**Scale/Scope**:
- Support 10k+ users
- 1-10 conversations per user average
- 10-50 messages per conversation average
- Message content up to 10,000 characters

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Phase II Requirements (Applicable)

✅ **Spec-Driven Development**: Specification created and validated in `specs/001-chatbot-schema/spec.md`

✅ **Technology Stack**:
- Using existing FastAPI backend
- Using existing SQLModel ORM
- Using existing Neon PostgreSQL database
- Using Alembic for migrations (standard tool for SQLModel/FastAPI)

✅ **Database Design**:
- Proper foreign key relationships defined
- Indexes on frequently queried columns
- Cascade deletes for referential integrity
- PostgreSQL-compatible data types

✅ **Stateless API Design**:
- No server-side session storage
- All conversation state persisted in database
- Each request fetches required context from database

✅ **Testing Requirements**:
- Unit tests for SQLModel models
- Integration tests for database operations
- Contract tests for schema validation

### Phase III Requirements (Applicable)

✅ **Conversation Database Schema**:
- `conversations` table with user_id, started_at, last_message_at
- `messages` table with conversation_id, role, content, created_at
- Foreign keys to existing `users` table
- Support for stateless chat endpoint pattern

✅ **No Constitution Violations**: All requirements align with established patterns

## Project Structure

### Documentation (this feature)

```text
specs/001-chatbot-schema/
├── plan.md              # This file (/sp.plan command output)
├── spec.md              # Feature specification (completed)
├── research.md          # Phase 0 output (to be generated)
├── data-model.md        # Phase 1 output (to be generated)
├── quickstart.md        # Phase 1 output (to be generated)
├── contracts/           # Phase 1 output (to be generated)
│   └── schema.sql       # SQL schema definition
├── checklists/
│   └── requirements.md  # Spec quality checklist (completed)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── alembic/
│   ├── versions/
│   │   └── xxxx_add_chatbot_schema.py  # NEW: Migration script
│   ├── env.py
│   └── alembic.ini
├── app/
│   ├── models/
│   │   ├── conversation.py              # NEW: Conversation model
│   │   └── message.py                   # NEW: Message model
│   ├── db.py                            # EXISTING: Database session
│   └── main.py                          # EXISTING: FastAPI app
└── tests/
    ├── models/
    │   ├── test_conversation.py         # NEW: Conversation model tests
    │   └── test_message.py              # NEW: Message model tests
    └── integration/
        └── test_chatbot_schema.py       # NEW: Integration tests
```

**Structure Decision**: Using "Option 2: Web application" structure. This feature extends the existing backend component with new database tables and models. No frontend changes required for this phase - frontend integration will come in subsequent features (MCP server, chat endpoint).

## Complexity Tracking

> No Constitution Check violations - this section not needed.

---

## Phase III: AI & MCP Server Design

> **This feature is the database foundation for AI chatbot - MCP tools and chat endpoint will be separate features**

### Database Schema (This Feature)

**Conversation Database Schema**:
```sql
-- conversations table
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_conversations_user_id (user_id)
);

-- messages table
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_messages_conversation_id (conversation_id)
);
```

**Stateless Design Support**:
This schema enables the stateless chat endpoint pattern:
1. Each chat request includes user_id and optional conversation_id
2. Backend fetches all messages for that conversation from database
3. Backend passes message history to AI agent
4. Backend stores new user message and AI response in database
5. No conversation state held in memory between requests

**Future Integration Points** (not in this feature):
- MCP Server will query these tables via SQLModel
- Chat endpoint will create/update conversations and messages
- Natural language processing will reference message history

---

## Implementation Phases

### Phase 0: Research & Technology Decisions

**Research Tasks**:

1. **Alembic Migration Best Practices**
   - Research: How to create migrations for new tables in existing database
   - Research: How to add foreign keys to existing tables safely
   - Research: How to handle migration rollback scenarios
   - Decision needed: Manual migration vs autogenerate

2. **SQLModel Foreign Key Patterns**
   - Research: Best practices for defining foreign key relationships in SQLModel
   - Research: Cascade delete configuration in SQLModel
   - Research: Index definition in SQLModel vs Alembic

3. **PostgreSQL Performance Optimization**
   - Research: Index strategies for conversation/message queries
   - Research: Timestamp precision for message ordering
   - Research: Text column sizing for large message content

4. **Testing Strategy**
   - Research: pytest-postgresql setup for integration tests
   - Research: Database fixture patterns for testing migrations
   - Research: Transaction rollback testing strategies

**Output**: `research.md` documenting all decisions with rationale

### Phase 1: Design & Data Modeling

**Data Model Design**:

Create `data-model.md` with detailed entity definitions:

1. **Conversation Entity**
   - Fields: id, user_id, started_at, last_message_at
   - Relationships: belongs_to User, has_many Messages
   - Validation: user_id must reference valid user
   - Indexes: user_id for fast user conversation lookups
   - Lifecycle: Created on first message, updated on each new message

2. **Message Entity**
   - Fields: id, conversation_id, role, content, created_at
   - Relationships: belongs_to Conversation
   - Validation: role must be 'user' or 'assistant', content non-empty
   - Indexes: conversation_id for fast message retrieval
   - Lifecycle: Immutable once created (no updates or deletes)

**API Contracts**:

Create `contracts/schema.sql` with:
- Complete DDL statements for both tables
- Foreign key constraints
- Check constraints
- Index definitions
- Comments documenting column purposes

**Quickstart Guide**:

Create `quickstart.md` for developers:
- How to run migrations locally
- How to create test conversations and messages
- How to query conversation history
- How to rollback migrations if needed

**Agent Context Update**:
Run `.specify/scripts/bash/update-agent-context.sh claude` to add:
- Alembic migration patterns
- SQLModel foreign key relationships
- Conversation/message model examples

### Phase 2: Task Breakdown

Will be generated by `/sp.tasks` command (not part of /sp.plan).

Expected task categories:
- Create SQLModel models (Conversation, Message)
- Create Alembic migration scripts
- Write unit tests for models
- Write integration tests for schema
- Update database initialization
- Document migration procedures

---

## Risk Analysis

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Migration fails on production database | HIGH | Test migration on staging database first; create rollback script; backup before migration |
| Foreign key constraints break existing data | HIGH | Verify users table exists and has correct structure; add FK with DEFERRABLE option initially |
| Performance degradation with large message history | MEDIUM | Add proper indexes; implement pagination for message retrieval; test with realistic data volumes |
| Concurrent write conflicts | MEDIUM | Use database transaction isolation; test concurrent message writes; implement retry logic |
| Migration doesn't apply cleanly | MEDIUM | Use Alembic autogenerate and review changes; test migration up and down paths |

### Mitigation Strategies

1. **Pre-migration Validation**: Check that `users` table exists with expected schema
2. **Staging Testing**: Run full migration on Neon staging database before production
3. **Rollback Plan**: Create downgrade migration that drops tables cleanly
4. **Performance Testing**: Load test with 1000 conversations and 10,000 messages
5. **Monitoring**: Add logging for migration execution time and success/failure

---

## Acceptance Criteria Summary

From the feature spec, this implementation must deliver:

✅ **FR-001**: `conversations` table created with specified columns
✅ **FR-002**: `messages` table created with specified columns
✅ **FR-003**: Foreign key from conversations.user_id to users.id
✅ **FR-004**: Foreign key from messages.conversation_id to conversations.id
✅ **FR-005**: Default NOW() on all timestamp fields
✅ **FR-006**: CHECK constraint on role field
✅ **FR-007**: Index on conversations.user_id
✅ **FR-008**: Index on messages.conversation_id
✅ **FR-009**: TEXT column for content (supports 10k+ characters)
✅ **FR-010**: Timestamp with millisecond precision
✅ **FR-011**: CASCADE DELETE on messages when conversation deleted
✅ **FR-012**: CASCADE DELETE on conversations when user deleted

✅ **SC-001**: Migration completes without errors
✅ **SC-002**: Query 100 conversations < 100ms
✅ **SC-003**: Query 50 messages < 50ms
✅ **SC-004**: Foreign keys prevent orphaned records
✅ **SC-005**: All queries use proper indexes
✅ **SC-006**: Concurrent writes handled correctly
✅ **SC-007**: Stateless pattern supported

---

## Next Steps After Planning

1. **Generate research.md**: Run Phase 0 research tasks
2. **Generate data-model.md**: Create detailed entity models
3. **Generate contracts/schema.sql**: Define complete SQL schema
4. **Generate quickstart.md**: Document migration procedures
5. **Run /sp.tasks**: Break down into actionable implementation tasks
6. **Run /sp.implement**: Execute task-by-task implementation
