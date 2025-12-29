# Tasks: ChatKit Conversational UI

**Feature**: 004-chatkit-ui | **Branch**: `004-chatkit-ui` | **Created**: 2025-12-28

## Overview

Build a custom conversational chat interface for the Next.js frontend using React components and Tailwind CSS. Connect to the existing backend chat endpoint from Feature 003. No external chat UI libraries required.

**Total Tasks**: 45
**User Stories**: 4 (P1-P4)
**Estimated Complexity**: Medium

---

## Task Summary by Phase

| Phase | Description | Task Count | Story |
|-------|-------------|------------|-------|
| 1 | Setup & Dependencies | 3 | N/A |
| 2 | Foundational (TypeScript types) | 4 | N/A |
| 3 | US1: Basic Chat Interaction | 12 | P1 |
| 4 | US2: Conversation History | 8 | P2 |
| 5 | US3: Streaming Responses | 10 | P3 |
| 6 | US4: Task Visual Feedback | 5 | P4 |
| 7 | Polish & Cross-Cutting | 3 | N/A |

---

## Phase 1: Setup & Dependencies

**Goal**: Verify environment and create necessary directory structure.

### Tasks

- [X] T001 Verify Next.js 15+ and React 19 installed in frontend/package.json
- [X] T002 Create chat components directory structure: frontend/components/chat/
- [X] T003 Create chat hooks directory: frontend/lib/hooks/ (if not exists)

**Completion Criteria**:
- All directories exist
- Package.json shows correct versions
- No new dependencies added (all packages already installed)

---

## Phase 2: Foundational (TypeScript Types)

**Goal**: Define shared TypeScript interfaces used across all user stories.

### Tasks

- [X] T004 [P] Create Message interface in frontend/types/chat.ts
- [X] T005 [P] Create ChatState interface in frontend/types/chat.ts
- [X] T006 [P] Create ChatRequest interface in frontend/types/chat.ts
- [X] T007 [P] Create ChatResponse interface in frontend/types/chat.ts

**Completion Criteria**:
- All TypeScript interfaces defined
- Proper types for role ('user' | 'assistant')
- Optional fields marked correctly
- No compilation errors

**Parallel Execution**: All T004-T007 can run in parallel (same file, different interfaces)

---

## Phase 3: User Story 1 - Basic Chat Interaction (P1)

**Story Goal**: Enable users to send natural language messages and receive AI responses for task management.

**Independent Test**: Type "add a task to buy groceries" and receive AI confirmation

**Why P1**: Core value proposition. Without basic chat, no other features matter.

### Tasks

- [X] T008 [US1] Create ChatInput component in frontend/components/chat/ChatInput.tsx
- [X] T009 [US1] Add input validation (prevent empty messages) in ChatInput component
- [X] T010 [US1] Add submit handler with Enter key support in ChatInput component
- [X] T011 [US1] Style ChatInput with Tailwind in ChatInput.tsx
- [X] T012 [P] [US1] Create ChatMessages component in frontend/components/chat/ChatMessages.tsx
- [X] T013 [US1] Implement message display with user/AI visual distinction in ChatMessages.tsx
- [X] T014 [US1] Add loading indicator in ChatMessages.tsx
- [X] T015 [US1] Implement auto-scroll to latest message in ChatMessages.tsx
- [X] T016 [US1] Create ChatInterface container in frontend/components/chat/ChatInterface.tsx
- [X] T017 [US1] Implement useChatState hook in frontend/lib/hooks/use-chat.ts
- [X] T018 [US1] Add API integration to send messages in use-chat.ts hook
- [X] T019 [US1] Create chat page with auth protection in frontend/app/chat/page.tsx

---

## Phase 4: User Story 2 - Conversation History Persistence (P2)

**Story Goal**: Display full conversation history across sessions.

**Independent Test**: Create conversation, close browser, reopen, see all previous messages.

**Dependencies**: Requires US1 (basic chat) to be complete.

### Tasks

- [X] T020 [US2] Add conversation_id state management in use-chat.ts hook
- [X] T021 [US2] Implement fetch conversation history on mount in use-chat.ts
- [X] T022 [US2] Add conversation_id to API requests in use-chat.ts
- [X] T023 [US2] Display historical messages in chronological order in ChatMessages.tsx
- [X] T024 [US2] Handle page reload with conversation persistence in chat/page.tsx
- [X] T025 [US2] Add scroll-independent history viewing in ChatMessages.tsx
- [X] T026 [US2] Implement 50-message display limit in ChatMessages.tsx
- [X] T027 [US2] Add conversation switching support in ChatInterface.tsx

---

## Phase 5: User Story 3 - Streaming AI Responses (P3)

**Story Goal**: Display AI responses progressively (word-by-word) for better perceived performance.

**Independent Test**: Send message and observe text appearing progressively vs. all at once.

**Dependencies**: Requires US1 (basic chat). US2 optional but recommended.

### Backend Tasks

- [ ] T028 [P] [US3] Create streaming endpoint in backend/app/routes/chat.py (/chat/stream)
- [ ] T029 [US3] Implement SSE event generator in chat.py streaming endpoint
- [ ] T030 [US3] Add OpenAI streaming support (stream=True) in chat.py
- [ ] T031 [US3] Configure StreamingResponse with proper headers in chat.py

### Frontend Tasks

- [ ] T032 [P] [US3] Create useStreamChat hook in frontend/lib/hooks/use-stream-chat.ts
- [ ] T033 [US3] Implement ReadableStream processing in use-stream-chat.ts
- [ ] T034 [US3] Add SSE message parsing in use-stream-chat.ts
- [ ] T035 [US3] Implement streaming state management in use-stream-chat.ts
- [ ] T036 [US3] Add progressive text display in ChatMessages.tsx
- [ ] T037 [US3] Add blinking cursor indicator for streaming in ChatMessages.tsx

---

## Phase 6: User Story 4 - Task Operation Visual Feedback (P4)

**Story Goal**: Update task list in real-time when AI performs task operations.

**Independent Test**: Ask AI to create task and see task appear in task list without refresh.

**Dependencies**: Requires US1 (basic chat). Assumes task list component exists.

### Tasks

- [ ] T038 [US4] Add task list refresh callback prop in ChatInterface.tsx
- [ ] T039 [US4] Detect tool_calls in chat response in use-chat.ts
- [ ] T040 [US4] Trigger task list refresh on add_task tool call in ChatInterface.tsx
- [ ] T041 [US4] Trigger task list refresh on update/complete/delete in ChatInterface.tsx
- [ ] T042 [US4] Add visual feedback toast notification in ChatInterface.tsx

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Error handling, edge cases, and final UX polish.

### Tasks

- [X] T043 Add error boundary in frontend/app/chat/error.tsx
- [X] T044 Add network error handling with retry in ChatInterface.tsx
- [X] T045 Add mobile responsive styling final polish in all chat components

---

## Implementation Strategy

### MVP Scope (Recommended First Iteration)

**Include**:
- Phase 1: Setup
- Phase 2: Foundational
- Phase 3: US1 - Basic Chat Interaction
- Phase 7: Basic Polish

**MVP Delivers**: Functional chat interface, send/receive messages, loading states, error handling

**Time to MVP**: 4-6 hours for experienced dev

### Incremental Delivery Plan

**Iteration 1** (MVP - 4-6h): T001-T019 + T043-T045 (Basic chat)
**Iteration 2** (+2-3h): T020-T027 (Add conversation history)
**Iteration 3** (+3-4h): T028-T037 (Add streaming responses)
**Iteration 4** (+1-2h): T038-T042 (Add task visual feedback)

**Total**: 10-15 hours for complete feature

---

**Tasks Status**: Ready for implementation via `/sp.implement`
**Total Tasks**: 45
**Critical Path Tasks**: 22 (Setup + Foundational + US1 + Polish)
**Enhancement Tasks**: 23 (US2 + US3 + US4)
