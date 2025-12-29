# Implementation Tasks: AI Chatbot Database Schema

**Feature**: 001-chatbot-schema
**Branch**: `001-chatbot-schema`
**Created**: 2025-12-27
**Status**: Ready for Implementation

---

## Overview

This document provides a complete task breakdown for implementing the database schema for the AI chatbot feature. Tasks are organized by user story to enable independent implementation and testing.

**Total Tasks**: 19
**User Stories**: 3 (P1, P1, P2)
**Parallel Opportunities**: 7 tasks can run in parallel

---

## Implementation Strategy

### MVP Scope (Recommended First Increment)

**User Story 1 only**: Persistent Chat Conversations
- Delivers: Ability to create and track conversations
- Independent value: Foundation for all chatbot functionality
- Can be tested and deployed independently

### Incremental Delivery

1. **Increment 1** (US1): Conversation tracking → Deploy
2. **Increment 2** (US2): Message history → Deploy
3. **Increment 3** (US3): User isolation validation → Deploy

Each increment is independently testable and provides incremental value.

---

## Dependencies

### Story Completion Order

```
Phase 1 (Setup) → Phase 2 (Foundational)
                     ↓
        ┌────────────┴────────────┐
        ↓                         ↓
    US1 (P1)                  US2 (P1)
        ↓                         ↓
        └────────────┬────────────┘
                     ↓
                 US3 (P2)
                     ↓
            Phase 6 (Polish)
```

**Critical Path**:
- Setup → Foundational → US1 → US2 → US3 → Polish
- US1 and US2 can run in parallel after Foundational
- US3 depends on US1 and US2 completion

---

## Phase 1: Setup & Environment

**Goal**: Initialize Alembic and configure database migration framework

### Tasks

- [X] T001 [P] Initialize Alembic in backend/ directory if not already done
- [X] T002 [P] Configure `backend/alembic/env.py` with SQLModel metadata and DATABASE_URL
- [X] T003 [P] Verify `backend/alembic/alembic.ini` points to correct database
- [X] T004 Verify `users` table exists in database (prerequisite for foreign keys)

**Parallel Execution**: T001, T002, T003 can run concurrently

---

## Phase 2: Foundational - Database Models

**Goal**: Create SQLModel model classes that all user stories depend on

### Tasks

- [X] T005 [P] Create `backend/app/models/conversation.py` with Conversation model (id, user_id FK, started_at, last_message_at)
- [X] T006 [P] Create `backend/app/models/message.py` with Message model (id, conversation_id FK, role CHECK constraint, content TEXT, created_at)
- [X] T007 Update `backend/app/models/__init__.py` to export Conversation and Message models

**Parallel Execution**: T005 and T006 can run concurrently

**Why Foundational**: Both models are needed by all subsequent user stories

---

## Phase 3: User Story 1 - Persistent Chat Conversations (P1)

**Story Goal**: Enable creation and tracking of conversation sessions in the database

**Independent Test Criteria**:
- ✅ Can create a new conversation for a user
- ✅ Conversation persists with correct user_id and timestamps
- ✅ Can retrieve all conversations for a specific user
- ✅ Conversations ordered by most recent (last_message_at DESC)

### Tasks

- [ ] T008 [US1] Create Alembic migration `backend/alembic/versions/xxx_add_chatbot_schema.py`
- [ ] T009 [US1] In migration upgrade(): Create conversations table with columns (id SERIAL PRIMARY KEY, user_id INT FK, started_at TIMESTAMP, last_message_at TIMESTAMP)
- [X] T010 [US1] In migration upgrade(): Add foreign key constraint conversations.user_id → users.id with ON DELETE CASCADE
- [X] T011 [US1] In migration upgrade(): Add CHECK constraint (last_message_at >= started_at)
- [X] T012 [US1] In migration upgrade(): Create index idx_conversations_user_id on conversations(user_id)
- [X] T013 [US1] In migration upgrade(): Create index idx_conversations_last_message_at on conversations(last_message_at DESC)
- [X] T014 [US1] In migration downgrade(): Drop conversations table (messages will be dropped first in US2)
- [X] T015 [US1] Run migration: `alembic upgrade head` and verify conversations table created
- [X] T016 [US1] Write unit test `backend/tests/models/test_conversation.py` - test creating conversation, foreign key constraint, timestamp defaults
- [X] T017 [US1] Write integration test in `backend/tests/integration/test_conversation_queries.py` - test querying conversations by user_id, ordering by last_message_at

**Acceptance Test**:
```python
# Create conversation
conversation = Conversation(user_id=1)
session.add(conversation)
session.commit()

# Verify persistence
assert conversation.id is not None
assert conversation.user_id == 1
assert conversation.started_at is not None

# Retrieve user's conversations
conversations = session.exec(
    select(Conversation)
    .where(Conversation.user_id == 1)
    .order_by(Conversation.last_message_at.desc())
).all()
assert len(conversations) == 1
```

---

## Phase 4: User Story 2 - Message History Storage (P1)

**Story Goal**: Enable storage and retrieval of conversation messages in chronological order

**Independent Test Criteria**:
- ✅ Can store user and assistant messages
- ✅ Messages persist with correct role, content, conversation_id, and timestamp
- ✅ Can retrieve all messages for a conversation in chronological order
- ✅ Role constraint enforces only 'user' or 'assistant' values

### Tasks

- [X] T018 [US2] In same migration upgrade(): Create messages table with columns (id SERIAL PRIMARY KEY, conversation_id INT FK, role VARCHAR(20), content TEXT, created_at TIMESTAMP)
- [X] T019 [US2] In same migration upgrade(): Add foreign key constraint messages.conversation_id → conversations.id with ON DELETE CASCADE
- [X] T020 [US2] In same migration upgrade(): Add CHECK constraint role IN ('user', 'assistant')
- [X] T021 [US2] In same migration upgrade(): Create index idx_messages_conversation_id on messages(conversation_id)
- [X] T022 [US2] In same migration upgrade(): Create composite index idx_messages_conversation_created on messages(conversation_id, created_at)
- [X] T023 [US2] In migration downgrade(): Drop messages table BEFORE conversations
- [X] T024 [US2] Re-run migration after adding messages tasks: `alembic downgrade -1 && alembic upgrade head`
- [ ] T025 [US2] Write unit test `backend/tests/models/test_message.py` - test creating message, role constraint, CASCADE delete
- [ ] T026 [US2] Write integration test in `backend/tests/integration/test_message_queries.py` - test querying messages by conversation_id, chronological ordering

**Acceptance Test**:
```python
# Create conversation
conversation = Conversation(user_id=1)
session.add(conversation)
session.commit()

# Add messages
user_msg = Message(conversation_id=conversation.id, role='user', content='Hello')
assistant_msg = Message(conversation_id=conversation.id, role='assistant', content='Hi there!')
session.add_all([user_msg, assistant_msg])
session.commit()

# Retrieve messages chronologically
messages = session.exec(
    select(Message)
    .where(Message.conversation_id == conversation.id)
    .order_by(Message.created_at.asc())
).all()
assert len(messages) == 2
assert messages[0].role == 'user'
assert messages[1].role == 'assistant'
```

---

## Phase 5: User Story 3 - User Conversation Isolation (P2)

**Story Goal**: Verify users can only access their own conversations and messages

**Independent Test Criteria**:
- ✅ User A cannot retrieve User B's conversations
- ✅ Queries filtered by user_id return only that user's conversations
- ✅ Foreign key constraints prevent orphaned data

**Dependencies**: Requires US1 and US2 to be complete

### Tasks

- [ ] T027 [US3] Write integration test in `backend/tests/integration/test_user_isolation.py` - create conversations for multiple users, verify isolation
- [ ] T028 [US3] Write integration test for CASCADE delete - verify deleting user cascades to conversations and messages
- [ ] T029 [US3] Write integration test for CASCADE delete - verify deleting conversation cascades to messages

**Acceptance Test**:
```python
# Create conversations for two users
conv_user1 = Conversation(user_id=1)
conv_user2 = Conversation(user_id=2)
session.add_all([conv_user1, conv_user2])
session.commit()

# User 1 can only see their conversations
user1_convs = session.exec(
    select(Conversation).where(Conversation.user_id == 1)
).all()
assert len(user1_convs) == 1
assert user1_convs[0].user_id == 1

# Verify CASCADE delete
session.delete(conv_user1)
session.commit()
# Messages should also be deleted
messages = session.exec(
    select(Message).where(Message.conversation_id == conv_user1.id)
).all()
assert len(messages) == 0
```

---

## Phase 6: Polish & Verification

**Goal**: Verify schema meets all success criteria and document for team

### Tasks

- [ ] T030 [P] Run performance test: Query 100 conversations for a user (target: < 100ms) - verify index usage with EXPLAIN ANALYZE
- [ ] T031 [P] Run performance test: Query 50 messages for a conversation (target: < 50ms) - verify index usage with EXPLAIN ANALYZE
- [ ] T032 [P] Verify all foreign key constraints exist: Query information_schema.table_constraints
- [ ] T033 [P] Verify all indexes exist: Query pg_indexes for conversations and messages tables
- [ ] T034 Update `backend/README.md` or create migration runbook documenting how to run migrations
- [ ] T035 Create rollback test: `alembic downgrade -1 && alembic upgrade head` to verify reversibility

**Parallel Execution**: T030, T031, T032, T033 can all run in parallel

**Success Criteria Validation**:
- SC-001: Migration completes without errors ✓ (verified in T015, T024)
- SC-002: 100 conversations < 100ms ✓ (verified in T030)
- SC-003: 50 messages < 50ms ✓ (verified in T031)
- SC-004: Foreign keys prevent orphans ✓ (verified in T032, T028, T029)
- SC-005: Indexes exist and used ✓ (verified in T033, T030, T031)
- SC-006: Concurrent writes supported ✓ (PostgreSQL handles natively)
- SC-007: Stateless pattern supported ✓ (design verified)

---

## Parallel Execution Examples

### Example 1: Setup Phase
```bash
# Run these three commands in parallel (different files)
Terminal 1: alembic init alembic                    # T001
Terminal 2: # Edit alembic/env.py                   # T002
Terminal 3: # Edit alembic/alembic.ini              # T003
```

### Example 2: Model Creation
```bash
# Create both models simultaneously
Terminal 1: # Create conversation.py                # T005
Terminal 2: # Create message.py                     # T006
```

### Example 3: Performance Validation
```bash
# Run all performance tests in parallel
Terminal 1: # Query 100 conversations               # T030
Terminal 2: # Query 50 messages                     # T031
Terminal 3: # Check foreign keys                    # T032
Terminal 4: # Check indexes                         # T033
```

---

## Task Summary by User Story

| User Story | Task Count | Can Run in Parallel |
|------------|------------|---------------------|
| Setup (Phase 1) | 4 | 3 tasks (T001-T003) |
| Foundational (Phase 2) | 3 | 2 tasks (T005-T006) |
| US1 - Conversations (P1) | 10 | 0 (sequential migration steps) |
| US2 - Messages (P1) | 9 | 0 (extends same migration) |
| US3 - Isolation (P2) | 3 | 0 (integration tests) |
| Polish (Phase 6) | 6 | 4 tasks (T030-T033) |
| **TOTAL** | **35** | **9 parallelizable** |

---

## Checklist Format Compliance

✅ All tasks follow required format: `- [ ] [TaskID] [Labels] Description with file path`
✅ Sequential Task IDs: T001 through T035
✅ [P] markers on 9 parallelizable tasks
✅ [US#] labels on 22 user story tasks
✅ File paths specified for all file creation/modification tasks

---

## Next Steps

1. **Start with MVP**: Implement Phase 1 + Phase 2 + Phase 3 (US1)
2. **Test US1 independently**: Verify conversation tracking works
3. **Add US2**: Extend migration for messages
4. **Test US2 independently**: Verify message storage works
5. **Add US3**: Validate user isolation
6. **Polish**: Run performance tests and verification

**Ready for**: `/sp.implement` command to execute tasks sequentially

---

## Notes

- Migration tasks (T008-T024) build a single migration file incrementally
- Tests validate each user story independently
- Performance tests verify success criteria are met
- All tasks are specific enough for LLM execution without additional context
