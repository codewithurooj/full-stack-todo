# Tasks: Stateless Chat Endpoint with OpenAI Agents SDK

**Input**: Design documents from `/specs/003-stateless-chat-endpoint/`
**Prerequisites**: plan.md (✅), spec.md (✅)
**Branch**: `003-stateless-chat-endpoint`

**Tests**: Tests are NOT explicitly requested in the spec, so test tasks are EXCLUDED per template guidance.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/app/`, `backend/tests/`
- All paths are relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add OpenAI SDK dependency to existing project

- [X] T001 Add openai>=1.0.0 to backend/requirements.txt
- [X] T002 Add OPENAI_API_KEY to backend/.env.example
- [X] T003 Update backend/app/config.py to include OPENAI_API_KEY and OPENAI_MODEL settings

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create ChatRequest Pydantic model in backend/app/routes/chat.py (message: str, conversation_id: Optional[int])
- [X] T005 [P] Create ChatResponse Pydantic model in backend/app/routes/chat.py (conversation_id: int, assistant_message: str, tool_calls: List[str], created_at: datetime)
- [X] T006 [P] Create get_all_tool_schemas() function in backend/app/mcp_server/server.py to generate OpenAI function schemas from 5 MCP tools
- [X] T007 Create OpenAI client instance in backend/app/routes/chat.py with API key from config
- [X] T008 Create FastAPI router for chat endpoint in backend/app/routes/chat.py
- [X] T009 Include chat router in backend/app/main.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Contextual AI Conversations (Priority: P1) 🎯 MVP

**Goal**: Enable users to have multi-turn conversations with AI that remembers full conversation context by fetching history from database

**Independent Test**: Send message "I need to buy groceries", then follow-up "When should I do that?", verify AI references groceries from first message

### Implementation for User Story 1

- [X] T010 [US1] Implement conversation retrieval logic: if conversation_id provided, fetch from database and validate ownership in backend/app/routes/chat.py
- [X] T011 [US1] Implement conversation creation logic: if conversation_id is None, create new Conversation record with user_id in backend/app/routes/chat.py
- [X] T012 [US1] Implement conversation history fetching: SELECT messages WHERE conversation_id ORDER BY created_at LIMIT 50 in backend/app/routes/chat.py
- [X] T013 [US1] Implement message array builder: system prompt + history messages + new user message in backend/app/routes/chat.py
- [X] T014 [US1] Store user message in database with role='user' before calling OpenAI in backend/app/routes/chat.py
- [X] T015 [US1] Implement OpenAI API call with messages array and empty tools list (no tool calling yet) in backend/app/routes/chat.py
- [X] T016 [US1] Store assistant response in database with role='assistant' after receiving from OpenAI in backend/app/routes/chat.py
- [X] T017 [US1] Update conversation.last_message_at timestamp after storing assistant message in backend/app/routes/chat.py
- [X] T018 [US1] Return ChatResponse with conversation_id, assistant_message, empty tool_calls, created_at in backend/app/routes/chat.py
- [X] T019 [US1] Add error handling for invalid conversation_id (404 Not Found) in backend/app/routes/chat.py
- [X] T020 [US1] Add error handling for conversation ownership mismatch (403 Forbidden) in backend/app/routes/chat.py
- [X] T021 [US1] Add input validation for message length (max 5,000 characters, return 400 if exceeded) in backend/app/routes/chat.py

**Checkpoint**: At this point, User Story 1 should be fully functional - users can have context-aware conversations

---

## Phase 4: User Story 2 - Tool-Augmented AI Responses (Priority: P1)

**Goal**: Enable AI to automatically invoke MCP tools (add_task, list_tasks, complete_task, delete_task, update_task) when users request task operations

**Independent Test**: Say "Create a task to call mom tomorrow", verify (1) AI invokes add_task, (2) task in database, (3) AI confirms creation

### Implementation for User Story 2

- [X] T022 [US2] Update OpenAI API call to include tool schemas from get_all_tool_schemas() with tool_choice="auto" in backend/app/routes/chat.py
- [X] T023 [US2] Implement tool call detection: check if response.choices[0].message.tool_calls exists in backend/app/routes/chat.py
- [X] T024 [US2] Implement tool invocation loop: for each tool_call, get handler from MCP server in backend/app/routes/chat.py
- [X] T025 [US2] Parse tool call arguments from OpenAI format to MCP tool request format in backend/app/routes/chat.py
- [X] T026 [US2] Execute MCP tool handler with parsed request, token_user_id, and session in backend/app/routes/chat.py
- [X] T027 [US2] Add tool result to messages array with role='tool', tool_call_id, and result JSON in backend/app/routes/chat.py
- [X] T028 [US2] Implement second OpenAI API call with updated messages including tool results in backend/app/routes/chat.py
- [X] T029 [US2] Update ChatResponse to include list of tool_calls invoked (tool names) in backend/app/routes/chat.py
- [X] T030 [US2] Add error handling for non-existent MCP tool requests in backend/app/routes/chat.py
- [X] T031 [US2] Add error handling for MCP tool execution failures in backend/app/routes/chat.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - AI can have conversations AND perform task operations

---

## Phase 5: User Story 3 - Concurrent User Isolation (Priority: P1)

**Goal**: Ensure complete data isolation between users - conversations and tool calls never leak across user boundaries

**Independent Test**: Create conversations for User A and User B, verify User A's AI responses only reference User A's data (never User B's)

### Implementation for User Story 3

- [X] T032 [US3] Add JWT token verification at endpoint start using verify_jwt_token from middleware in backend/app/routes/chat.py
- [X] T033 [US3] Verify user_id path parameter matches token_user_id, return 403 if mismatch in backend/app/routes/chat.py
- [X] T034 [US3] Ensure conversation history query filters by user_id from JWT token in backend/app/routes/chat.py
- [X] T035 [US3] Verify all MCP tool calls receive token_user_id (not path user_id) for authorization in backend/app/routes/chat.py
- [X] T036 [US3] Add logging for all chat requests with user_id, conversation_id, message_id for audit trail in backend/app/routes/chat.py

**Checkpoint**: All 3 P1 user stories complete - core chatbot functionality ready with full security

---

## Phase 6: User Story 4 - Stateless Scalability (Priority: P2)

**Goal**: Ensure zero in-memory state so application can scale horizontally and recover instantly from server restarts

**Independent Test**: Send message, restart server, send another message in same conversation, verify AI has full context

### Implementation for User Story 4

- [X] T037 [US4] Verify no global state variables exist in backend/app/routes/chat.py (code review)
- [X] T038 [US4] Verify all conversation context fetched from database on each request in backend/app/routes/chat.py (code review)
- [X] T039 [US4] Verify OpenAI client is stateless (recreated or singleton without state) in backend/app/routes/chat.py
- [X] T040 [US4] Add performance logging for database fetch time (<100ms target) in backend/app/routes/chat.py
- [X] T041 [US4] Add performance logging for total request time (<3s p95 target) in backend/app/routes/chat.py

**Checkpoint**: Stateless design verified - application ready for horizontal scaling

---

## Phase 7: User Story 5 - Error Recovery and Graceful Degradation (Priority: P3)

**Goal**: Provide clear, helpful error messages for all failure modes

**Independent Test**: Simulate OpenAI API failure, verify endpoint returns clear message "AI service temporarily unavailable"

### Implementation for User Story 5

- [X] T042 [US5] Add try-except for OpenAI API errors with user-friendly message in backend/app/routes/chat.py
- [X] T043 [US5] Implement OpenAI API timeout (30 seconds) and handle TimeoutError in backend/app/routes/chat.py
- [X] T044 [US5] Ensure user message is saved to database even if OpenAI call fails in backend/app/routes/chat.py
- [X] T045 [US5] Add try-except for database errors with 503 Service Unavailable response in backend/app/routes/chat.py
- [X] T046 [US5] Improve error message for message length validation (explain 5,000 char limit) in backend/app/routes/chat.py
- [X] T047 [US5] Add error handling for conversation not found (clear 404 message) in backend/app/routes/chat.py
- [X] T048 [US5] Add error handling for unauthorized access (clear 403 message) in backend/app/routes/chat.py

**Checkpoint**: All user stories complete - production-ready chat endpoint with comprehensive error handling

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T049 Add system prompt configuration to backend/app/config.py (default: "You are a helpful AI assistant for task management...")
- [X] T050 Add conversation history window size configuration (default: 50 messages) to backend/app/config.py
- [X] T051 [P] Add docstrings to all functions in backend/app/routes/chat.py
- [X] T052 [P] Add type hints to all function parameters and return values in backend/app/routes/chat.py
- [X] T053 Run mypy type checking on backend/app/routes/chat.py
- [X] T054 Run ruff linting on backend/app/routes/chat.py
- [X] T055 [P] Update backend/CLAUDE.md with chat endpoint patterns and examples
- [X] T056 Create quickstart.md with curl examples for testing chat endpoint in specs/003-stateless-chat-endpoint/
- [X] T057 Verify all functional requirements (FR-001 through FR-020) are implemented
- [X] T058 Verify all success criteria (SC-001 through SC-010) can be measured

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational - No dependencies on other stories
  - User Story 2 (P1): Depends on User Story 1 completion (extends chat with tool calling)
  - User Story 3 (P1): Can run in parallel with US1/US2 (different concerns - security)
  - User Story 4 (P2): Can run in parallel with US1/US2/US3 (code review + logging)
  - User Story 5 (P3): Depends on US1/US2 completion (adds error handling to existing flow)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Foundation only - implements basic chat
- **User Story 2 (P1)**: **Depends on US1** - extends chat endpoint with tool calling
- **User Story 3 (P1)**: Foundation only - adds security to endpoint (can run parallel with US1/US2)
- **User Story 4 (P2)**: Foundation only - verifies stateless design (can run parallel)
- **User Story 5 (P3)**: **Depends on US1/US2** - adds error handling to complete flow

### Within Each User Story

- Tasks are ordered sequentially within each story
- Must complete in order (each task builds on previous)
- Story complete when all tasks for that story are done

### Parallel Opportunities

**Phase 2 (Foundational)**:
- T004, T005, T006 can run in parallel (different models/functions)

**Phase 3 (User Story 1)**:
- All tasks sequential (building chat endpoint step-by-step)

**Phase 4 (User Story 2)**:
- All tasks sequential (extending US1 endpoint)

**Phase 5 (User Story 3)**:
- Can run entirely in parallel with US4 (different concerns)

**Phase 6 (User Story 4)**:
- Can run entirely in parallel with US3 (different concerns)

**Phase 8 (Polish)**:
- T051, T052, T055 can run in parallel (different files/concerns)

---

## Parallel Example: Foundational Phase

```bash
# Launch all foundational tasks together:
Task: "Create ChatRequest Pydantic model"
Task: "Create ChatResponse Pydantic model"
Task: "Create get_all_tool_schemas() function"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (3 tasks)
2. Complete Phase 2: Foundational (6 tasks) - CRITICAL blocker
3. Complete Phase 3: User Story 1 (12 tasks)
4. **STOP and VALIDATE**: Test basic chat with context
5. **MVP Complete!** Can have contextual AI conversations

### Incremental Delivery

1. **MVP** (Setup + Foundation + US1): Basic contextual chat
2. **MVP + US2**: Chat with task management tools
3. **MVP + US2 + US3**: Full security and user isolation
4. **MVP + US2 + US3 + US4**: Production-ready scalability
5. **MVP + US2 + US3 + US4 + US5**: Complete error handling

### Recommended Sequence

**Priority 1** (Core functionality):
1. Phase 1: Setup (T001-T003)
2. Phase 2: Foundational (T004-T009)
3. Phase 3: User Story 1 (T010-T021) - Basic chat
4. Phase 4: User Story 2 (T022-T031) - Tool calling
5. Phase 5: User Story 3 (T032-T036) - Security

**Priority 2** (Production hardening):
6. Phase 6: User Story 4 (T037-T041) - Scalability verification
7. Phase 7: User Story 5 (T042-T048) - Error handling

**Priority 3** (Polish):
8. Phase 8: Polish (T049-T058) - Documentation and cleanup

---

## Task Summary

**Total Tasks**: 58
- **Setup**: 3 tasks
- **Foundational**: 6 tasks (BLOCKING)
- **User Story 1 (P1)**: 12 tasks - Basic contextual chat
- **User Story 2 (P1)**: 10 tasks - Tool-augmented responses
- **User Story 3 (P1)**: 5 tasks - User isolation & security
- **User Story 4 (P2)**: 5 tasks - Stateless scalability
- **User Story 5 (P3)**: 7 tasks - Error recovery
- **Polish**: 10 tasks

**Parallel Opportunities**: 6 tasks marked [P] (10% of total)

**MVP Scope** (Minimum Viable Product):
- Phase 1-3 only = 21 tasks (36% of total)
- Delivers: Basic AI chat with conversation context

**Production Scope** (All P1 stories):
- Phase 1-5 = 36 tasks (62% of total)
- Delivers: Full-featured chatbot with security

---

## Notes

- Tests NOT included (not requested in spec)
- [P] tasks = different files/functions, no dependencies
- [Story] label maps task to specific user story for traceability
- User Story 2 extends User Story 1 (same file, sequential)
- User Story 3 can run parallel to US1/US2 (security concerns)
- Commit after each logical group of tasks
- All tasks in backend/app/routes/chat.py (single file implementation)
