# Implementation Tasks: MCP Server with 5 Custom Tools

**Feature**: 002-mcp-server
**Branch**: 002-mcp-server
**Created**: 2025-12-27
**Status**: Ready for Implementation

---

## Overview

Complete task breakdown for implementing MCP server with 5 stateless tools for AI-powered task management.

**Total Tasks**: 47
**User Stories**: 5 (P1: US1, P1: US2, P2: US3, P2: US4, P3: US5)
**Parallel Opportunities**: 9 tasks

---

## Implementation Strategy

### MVP Scope
**US1 + US2**: AI task creation and viewing (P1 stories)

### Incremental Delivery
1. Increment 1 (US1+US2): Creation and viewing
2. Increment 2 (US3): Completion
3. Increment 3 (US4): Updates
4. Increment 4 (US5): Deletion

---

## Phase 1: Setup & Environment

- [x] T001 [P] Install MCP SDK in backend/requirements.txt: mcp>=0.9.0
- [x] T002 [P] Install OpenAI SDK in backend/requirements.txt: openai>=1.0.0
- [x] T003 [P] Install slowapi in backend/requirements.txt: slowapi>=0.1.9
- [x] T004 Add OPENAI_API_KEY to backend/.env.example
- [x] T005 Create backend/app/config.py with OpenAI configuration
- [x] T006 Verify database schema has required tables

---

## Phase 2: Foundational - Shared Infrastructure

- [x] T007 [P] Create backend/app/mcp_server/__init__.py
- [x] T008 [P] Create backend/app/mcp_server/errors.py with MCPError class
- [x] T009 [P] Create backend/app/mcp_server/validation.py with shared validation
- [x] T010 Create backend/app/mcp_server/auth.py with JWT verification
- [x] T011 [P] Create backend/app/mcp_server/tools/__init__.py

---

## Phase 3: US1 - AI-Assisted Task Creation (P1)

**Independent Test**: Say "I need to buy groceries" -> Task created

- [x] T012 [US1] Create backend/app/mcp_server/tools/add_task.py with AddTaskRequest
- [x] T013 [US1] Implement add_task tool with DB INSERT and user isolation
- [x] T014 [US1] Add rate limiting to add_task (100/hour)
- [x] T015 [US1] Register add_task in backend/app/mcp_server/server.py
- [x] T016 [US1] Add POST /mcp/tools/add_task in backend/app/routes/mcp.py

---

## Phase 4: US2 - Conversational Task Viewing (P1)

**Independent Test**: Ask "What tasks do I have?" -> Lists tasks

- [x] T017 [US2] Create backend/app/mcp_server/tools/list_tasks.py with ListTasksRequest
- [x] T018 [US2] Implement list_tasks tool with DB SELECT and filtering
- [x] T019 [US2] Add rate limiting to list_tasks (1000/hour)
- [x] T020 [US2] Register list_tasks in backend/app/mcp_server/server.py
- [x] T021 [US2] Add GET /mcp/tools/list_tasks in backend/app/routes/mcp.py

---

## Phase 5: US3 - Natural Language Task Completion (P2)

**Independent Test**: Say "I finished buying groceries" -> Task completed

- [x] T022 [US3] Create backend/app/mcp_server/tools/complete_task.py
- [x] T023 [US3] Implement complete_task tool with toggle logic
- [x] T024 [US3] Add rate limiting to complete_task (200/hour)
- [x] T025 [US3] Register complete_task in server.py
- [x] T026 [US3] Add PATCH /mcp/tools/complete_task in mcp.py

---

## Phase 6: US4 - Conversational Task Updates (P2)

**Independent Test**: Say "Update task to include dinner" -> Task modified

- [x] T027 [US4] Create backend/app/mcp_server/tools/update_task.py
- [x] T028 [US4] Implement update_task tool with UPDATE logic
- [x] T029 [US4] Add rate limiting to update_task (200/hour)
- [x] T030 [US4] Register update_task in server.py
- [x] T031 [US4] Add PUT /mcp/tools/update_task in mcp.py

---

## Phase 7: US5 - AI-Powered Task Deletion (P3)

**Independent Test**: Say "Delete the grocery task" -> Task removed

- [x] T032 [US5] Create backend/app/mcp_server/tools/delete_task.py
- [x] T033 [US5] Implement delete_task tool with DELETE logic
- [x] T034 [US5] Add rate limiting to delete_task (100/hour)
- [x] T035 [US5] Register delete_task in server.py
- [x] T036 [US5] Add DELETE /mcp/tools/delete_task in mcp.py

---

## Phase 8: Chat Endpoint Integration

- [x] T037 Create backend/app/routes/chat.py with ChatRequest model
- [x] T038 Implement POST /api/{user_id}/chat with 8-step stateless flow
- [x] T039 Configure OpenAI client with all 5 tool schemas
- [x] T040 Implement tool callback handlers
- [x] T041 Add chat endpoint to backend/app/main.py

---

## Phase 9: Polish & Verification

- [x] T042 [P] Add logging for all tool calls in server.py
- [x] T043 [P] Update backend/CLAUDE.md with MCP patterns
- [x] T044 Test rate limiting (101 creates reject, 99 success)
- [x] T045 Test cross-user isolation (expect 403)
- [x] T046 Test all tools with natural language commands
- [x] T047 Update .env.example and README with setup instructions

---

## Task Summary

| Phase | Tasks | Parallel |
|-------|-------|----------|
| Setup | 6 | 3 |
| Foundational | 5 | 4 |
| US1 (P1) | 5 | 0 |
| US2 (P1) | 5 | 0 |
| US3 (P2) | 5 | 0 |
| US4 (P2) | 5 | 0 |
| US5 (P3) | 5 | 0 |
| Chat | 5 | 0 |
| Polish | 6 | 2 |
| TOTAL | 47 | 9 |

---

Ready for /sp.implement to execute tasks
