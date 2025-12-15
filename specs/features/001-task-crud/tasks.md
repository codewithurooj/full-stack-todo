# Tasks: Task CRUD Operations

**Input**: Design documents from `/specs/features/001-task-crud/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/tasks.openapi.yml

**Tests**: Backend tests with pytest are included as this is a production application requiring quality assurance.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US5)
- All file paths are relative to repository root

## Path Conventions

- **Backend**: `backend/app/`, `backend/tests/`, `backend/migrations/`
- **Frontend**: `frontend/app/`, `frontend/components/`, `frontend/lib/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and monorepo structure

- [ ] T001 Verify Neon PostgreSQL database is created and connection string is available
- [ ] T002 Create backend/.env file with DATABASE_URL and BETTER_AUTH_SECRET (32+ char random string)
- [ ] T003 Create frontend/.env.local file with NEXT_PUBLIC_API_URL and BETTER_AUTH_SECRET (same as backend)
- [ ] T004 [P] Install backend dependencies: pip install fastapi sqlmodel pydantic python-jose passlib alembic pytest httpx pytest-asyncio
- [ ] T005 [P] Install frontend dependencies: npm install in frontend/ directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Backend Foundation

- [ ] T006 [P] Create backend/app/__init__.py (empty file)
- [ ] T007 [P] Implement backend/app/config.py with environment variables (DATABASE_URL, BETTER_AUTH_SECRET, ALLOWED_ORIGINS)
- [ ] T008 [P] Implement backend/app/database.py with SQLModel engine and get_session dependency
- [ ] T009 Initialize Alembic in backend/ with: alembic init migrations
- [ ] T010 Configure backend/migrations/env.py for SQLModel support and Neon PostgreSQL connection
- [ ] T011 [P] Create backend/app/models/__init__.py (empty file)
- [ ] T012 [P] Create backend/app/models/user.py with User SQLModel matching Better Auth schema
- [ ] T013 [P] Create backend/app/models/task.py with Task SQLModel per data-model.md
- [ ] T014 Generate initial migration: alembic revision --autogenerate -m "Initial schema"
- [ ] T015 Review and apply migration: alembic upgrade head
- [ ] T016 [P] Create backend/app/schemas/__init__.py (empty file)
- [ ] T017 [P] Implement backend/app/schemas/common.py with ResponseMeta and DataResponse wrappers
- [ ] T018 [P] Create backend/app/middleware/__init__.py (empty file)
- [ ] T019 Implement backend/app/middleware/auth.py with JWT verification dependency (get_current_user)
- [ ] T020 [P] Create backend/app/routes/__init__.py (empty file)
- [ ] T021 Implement backend/app/main.py with FastAPI app, CORS middleware, and router registration
- [ ] T022 Verify backend starts: uvicorn app.main:app --reload (should run without errors)

### Frontend Foundation

- [ ] T023 [P] Create frontend/lib/auth.ts with Better Auth configuration
- [ ] T024 [P] Create frontend/lib/api/client.ts with base fetch wrapper (includes auth headers)
- [ ] T025 [P] Create frontend/types/task.ts with Task, TaskCreate, TaskUpdate TypeScript interfaces
- [ ] T026 [P] Implement frontend/app/layout.tsx with Better Auth provider
- [ ] T027 [P] Create frontend/app/api/auth/[...all]/route.ts for Better Auth API routes
- [ ] T028 [P] Create frontend/app/auth/signin/page.tsx for signin page
- [ ] T029 [P] Create frontend/app/auth/signup/page.tsx for signup page
- [ ] T030 [P] Create frontend/components/Navbar.tsx with auth state display and signout button
- [ ] T031 Verify frontend starts: npm run dev (should run without errors)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Create New Task (Priority: P1) 🎯 MVP

**Goal**: Enable users to create new tasks with title and optional description

**Independent Test**: Create a task with title "Test Task" and description "Test Description", verify it appears in the database and can be retrieved via API

### Backend - User Story 1

- [ ] T032 [P] [US1] Create backend/app/schemas/task.py with TaskCreate, TaskUpdate, TaskResponse schemas
- [ ] T033 [US1] Implement POST /api/{user_id}/tasks endpoint in backend/app/routes/tasks.py
- [ ] T034 [US1] Add validation for title (required, 1-200 chars) and description (optional, max 1000 chars)
- [ ] T035 [US1] Ensure user_id from JWT matches path parameter (403 if mismatch)
- [ ] T036 [US1] Test task creation with pytest: backend/tests/test_tasks.py::test_create_task_success
- [ ] T037 [US1] Test validation errors: backend/tests/test_tasks.py::test_create_task_invalid_title
- [ ] T038 [US1] Test unauthorized access: backend/tests/test_tasks.py::test_create_task_unauthorized

### Frontend - User Story 1

- [ ] T039 [P] [US1] Create frontend/lib/api/tasks.ts with createTask function
- [ ] T040 [US1] Create frontend/components/TaskForm.tsx with create form (title input, description textarea, submit button)
- [ ] T041 [US1] Create frontend/app/tasks/new/page.tsx using TaskForm component
- [ ] T042 [US1] Add form validation (title required, max lengths)
- [ ] T043 [US1] Add loading state during submission
- [ ] T044 [US1] Add error handling with user-friendly messages
- [ ] T045 [US1] Redirect to /tasks after successful creation
- [ ] T046 [US1] Add "Create Task" link to Navbar

**Checkpoint**: Users can now create tasks. Test independently: signup → signin → create task → verify in database

---

## Phase 4: User Story 2 - View Task List (Priority: P2)

**Goal**: Enable users to see all their tasks in a list with completion status

**Independent Test**: Create 3 tasks (2 incomplete, 1 complete), verify all 3 appear in list with correct status indicators

### Backend - User Story 2

- [ ] T047 [P] [US2] Implement GET /api/{user_id}/tasks endpoint in backend/app/routes/tasks.py
- [ ] T048 [US2] Add filtering by completed status (query param: ?completed=true/false)
- [ ] T049 [US2] Add sorting by created_at, updated_at, title (query params: ?sort=field&order=asc/desc)
- [ ] T050 [US2] Add pagination support (query params: ?limit=50&offset=0)
- [ ] T051 [US2] Ensure tasks are filtered by user_id (user isolation)
- [ ] T052 [US2] Return tasks in reverse chronological order by default (newest first)
- [ ] T053 [US2] Test list all tasks: backend/tests/test_tasks.py::test_list_tasks_success
- [ ] T054 [US2] Test empty list: backend/tests/test_tasks.py::test_list_tasks_empty
- [ ] T055 [US2] Test filtering: backend/tests/test_tasks.py::test_list_tasks_filtered
- [ ] T056 [US2] Test user isolation: backend/tests/test_tasks.py::test_list_tasks_user_isolation

### Frontend - User Story 2

- [ ] T057 [P] [US2] Add listTasks function to frontend/lib/api/tasks.ts
- [ ] T058 [P] [US2] Create frontend/components/ui/card.tsx using shadcn/ui (for task cards)
- [ ] T059 [P] [US2] Create frontend/components/ui/checkbox.tsx using shadcn/ui (for completion status)
- [ ] T060 [US2] Create frontend/components/TaskItem.tsx to display individual task (title, description, completed status, timestamps)
- [ ] T061 [US2] Create frontend/components/TaskList.tsx to display array of tasks
- [ ] T062 [US2] Create frontend/app/tasks/page.tsx as main task list view
- [ ] T063 [US2] Add loading state with skeleton UI
- [ ] T064 [US2] Add empty state message when no tasks exist
- [ ] T065 [US2] Add visual distinction for completed vs incomplete tasks (strikethrough, different color)
- [ ] T066 [US2] Add error handling for API failures

**Checkpoint**: Users can view their task list. Test independently: create multiple tasks → view list → verify all appear with correct status

---

## Phase 5: User Story 3 - Update Existing Task (Priority: P3)

**Goal**: Enable users to edit task title and description

**Independent Test**: Create task → edit title and description → verify changes are persisted and displayed

### Backend - User Story 3

- [ ] T067 [P] [US3] Implement PUT /api/{user_id}/tasks/{id} endpoint in backend/app/routes/tasks.py
- [ ] T068 [US3] Support partial updates (only provided fields are updated)
- [ ] T069 [US3] Validate title if provided (1-200 chars, not empty)
- [ ] T070 [US3] Validate description if provided (max 1000 chars)
- [ ] T071 [US3] Return 404 if task doesn't exist or doesn't belong to user
- [ ] T072 [US3] Update updated_at timestamp automatically
- [ ] T073 [US3] Test update task: backend/tests/test_tasks.py::test_update_task_success
- [ ] T074 [US3] Test partial update: backend/tests/test_tasks.py::test_update_task_partial
- [ ] T075 [US3] Test validation: backend/tests/test_tasks.py::test_update_task_invalid
- [ ] T076 [US3] Test not found: backend/tests/test_tasks.py::test_update_task_not_found

### Frontend - User Story 3

- [ ] T077 [P] [US3] Add updateTask function to frontend/lib/api/tasks.ts
- [ ] T078 [US3] Add edit mode state to TaskForm component (title: "Edit Task" vs "Create Task")
- [ ] T079 [US3] Create frontend/app/tasks/[id]/edit/page.tsx for edit view
- [ ] T080 [US3] Pre-fill form with existing task data
- [ ] T081 [US3] Add cancel button to discard changes
- [ ] T082 [US3] Validate changes before submission
- [ ] T083 [US3] Show loading state during update
- [ ] T084 [US3] Redirect to /tasks after successful update
- [ ] T085 [US3] Add "Edit" button to TaskItem component
- [ ] T086 [US3] Add optimistic update (update UI immediately, rollback on error)

**Checkpoint**: Users can edit tasks. Test independently: create task → click edit → change title/description → save → verify changes

---

## Phase 6: User Story 4 - Delete Task (Priority: P4)

**Goal**: Enable users to permanently delete tasks

**Independent Test**: Create task → delete it → verify it no longer appears in list or database

### Backend - User Story 4

- [ ] T087 [P] [US4] Implement DELETE /api/{user_id}/tasks/{id} endpoint in backend/app/routes/tasks.py
- [ ] T088 [US4] Return 204 No Content on successful deletion
- [ ] T089 [US4] Return 404 if task doesn't exist or doesn't belong to user
- [ ] T090 [US4] Ensure user_id from JWT matches authenticated user
- [ ] T091 [US4] Test delete task: backend/tests/test_tasks.py::test_delete_task_success
- [ ] T092 [US4] Test not found: backend/tests/test_tasks.py::test_delete_task_not_found
- [ ] T093 [US4] Test unauthorized: backend/tests/test_tasks.py::test_delete_task_unauthorized

### Frontend - User Story 4

- [ ] T094 [P] [US4] Add deleteTask function to frontend/lib/api/tasks.ts
- [ ] T095 [P] [US4] Create frontend/components/ui/dialog.tsx using shadcn/ui (for confirmation)
- [ ] T096 [US4] Create frontend/components/DeleteConfirmDialog.tsx with confirmation message
- [ ] T097 [US4] Add "Delete" button to TaskItem component
- [ ] T098 [US4] Show confirmation dialog before deletion
- [ ] T099 [US4] Remove task from UI immediately after confirmation (optimistic update)
- [ ] T100 [US4] Show error message if deletion fails and restore task to list
- [ ] T101 [US4] Add loading state during deletion

**Checkpoint**: Users can delete tasks. Test independently: create task → click delete → confirm → verify task removed from list

---

## Phase 7: User Story 5 - Mark Task Complete (Priority: P5)

**Goal**: Enable users to toggle task completion status

**Independent Test**: Create task → mark complete → verify status changes → mark incomplete → verify status reverts

### Backend - User Story 5

- [ ] T102 [P] [US5] Implement PATCH /api/{user_id}/tasks/{id}/complete endpoint in backend/app/routes/tasks.py
- [ ] T103 [US5] Toggle completed field (true ↔ false)
- [ ] T104 [US5] Update updated_at timestamp
- [ ] T105 [US5] Return updated task with new status
- [ ] T106 [US5] Return 404 if task doesn't exist or doesn't belong to user
- [ ] T107 [US5] Test toggle complete: backend/tests/test_tasks.py::test_toggle_complete_success
- [ ] T108 [US5] Test multiple toggles: backend/tests/test_tasks.py::test_toggle_complete_multiple
- [ ] T109 [US5] Test not found: backend/tests/test_tasks.py::test_toggle_complete_not_found

### Frontend - User Story 5

- [ ] T110 [P] [US5] Add toggleTaskComplete function to frontend/lib/api/tasks.ts
- [ ] T111 [US5] Add checkbox to TaskItem component for completion status
- [ ] T112 [US5] Update completed status on checkbox click
- [ ] T113 [US5] Apply visual changes immediately (optimistic update)
- [ ] T114 [US5] Rollback visual changes if API call fails
- [ ] T115 [US5] Add loading/disabled state during toggle
- [ ] T116 [US5] Update task list to reflect new status without full refresh

**Checkpoint**: Users can toggle task completion. Test independently: create task → toggle complete → verify visual change → toggle again → verify revert

---

## Phase 8: Get Task Details (Supporting Feature)

**Goal**: Enable users to view full task details (supports US2)

**Independent Test**: Create task with long description → click to view details → verify full title and description are displayed

### Backend - User Story (Supporting)

- [ ] T117 [P] Implement GET /api/{user_id}/tasks/{id} endpoint in backend/app/routes/tasks.py
- [ ] T118 Return full task details with all fields
- [ ] T119 Return 404 if task doesn't exist or doesn't belong to user
- [ ] T120 Test get task: backend/tests/test_tasks.py::test_get_task_success
- [ ] T121 Test not found: backend/tests/test_tasks.py::test_get_task_not_found

### Frontend - User Story (Supporting)

- [ ] T122 [P] Add getTask function to frontend/lib/api/tasks.ts
- [ ] T123 Create frontend/app/tasks/[id]/page.tsx for task detail view
- [ ] T124 Display full task information (title, description, status, timestamps)
- [ ] T125 Add "Back to List" navigation
- [ ] T126 Add loading state
- [ ] T127 Add error handling for task not found

**Checkpoint**: Users can view task details. Test independently: create task → click task → view details → verify all fields displayed

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### UI/UX Enhancements

- [ ] T128 [P] Add frontend/components/ui/button.tsx using shadcn/ui (consistent button styles)
- [ ] T129 [P] Add frontend/components/ui/input.tsx using shadcn/ui (consistent input styles)
- [ ] T130 [P] Implement toast notifications for success/error messages using a toast library
- [ ] T131 [P] Add loading skeletons for task list and forms
- [ ] T132 [P] Implement responsive design for mobile devices (Tailwind breakpoints)
- [ ] T133 Add keyboard shortcuts (Enter to submit forms, Esc to close dialogs)

### Backend Improvements

- [ ] T134 [P] Add comprehensive error logging in backend/app/main.py
- [ ] T135 [P] Add request/response logging middleware
- [ ] T136 [P] Implement rate limiting for API endpoints (100 req/min per user)
- [ ] T137 Add health check endpoint: GET /health

### Testing & Quality

- [ ] T138 [P] Add backend/tests/conftest.py with pytest fixtures (test database, auth tokens)
- [ ] T139 [P] Ensure all backend tests pass: pytest backend/tests/
- [ ] T140 [P] Add backend test coverage report: pytest --cov=app --cov-report=html
- [ ] T141 Verify test coverage is above 80%

### Documentation

- [ ] T142 [P] Create backend/README.md with setup instructions
- [ ] T143 [P] Create frontend/README.md with setup instructions
- [ ] T144 [P] Update root README.md with project overview and quickstart
- [ ] T145 Create .env.example files for both backend and frontend

### Deployment Preparation

- [ ] T146 [P] Create backend/Procfile for Render deployment
- [ ] T147 [P] Create backend/requirements.txt from current environment
- [ ] T148 [P] Configure frontend/next.config.js for production build
- [ ] T149 Test backend production build: docker build -t todo-backend backend/
- [ ] T150 Test frontend production build: npm run build in frontend/
- [ ] T151 Configure CORS for production frontend URL in backend
- [ ] T152 Set up Neon connection pooling for production

### Final Validation

- [ ] T153 Run through quickstart.md end-to-end locally
- [ ] T154 Test all 5 user stories work together (signup → create → view → edit → delete → toggle)
- [ ] T155 Verify user data isolation (create second user, ensure tasks are separate)
- [ ] T156 Test error scenarios (invalid input, network errors, auth errors)
- [ ] T157 Verify performance: create 100 tasks, ensure list loads in < 2 seconds

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - **US1 (P1)**: Can start after Phase 2 - No dependencies on other stories
  - **US2 (P2)**: Can start after Phase 2 - Independent (but nicer with US1 existing)
  - **US3 (P3)**: Can start after Phase 2 - Independent (but requires US2 to see changes)
  - **US4 (P4)**: Can start after Phase 2 - Independent (but requires US2 to see removal)
  - **US5 (P5)**: Can start after Phase 2 - Independent (but requires US2 to see status)
  - **Get Details**: Can start after Phase 2 - Supports US2
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### Within Each User Story

- Backend tasks before frontend tasks (API must exist before UI calls it)
- Tests can be written in parallel with implementation
- Models before routes
- Routes before frontend API client functions
- API client functions before UI components
- Core implementation before integration

### Parallel Opportunities

**Phase 1 (Setup)**: T004 and T005 can run in parallel

**Phase 2 (Foundational)**:
- Backend: T006-T008, T011-T013, T016-T018, T020 all parallel
- Frontend: T023-T030 all parallel after backend is running

**User Stories (Phases 3-8)**: Once Phase 2 completes:
- All user stories (US1-US5 + Get Details) can start in parallel
- Within each story, tasks marked [P] can run in parallel

**Phase 9 (Polish)**: Most tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1 (Create Task)

```bash
# Backend tasks that can run in parallel:
Task T032: "Create backend/app/schemas/task.py"
Task T036-T038: All test files (different test functions)

# Frontend tasks that can run in parallel:
Task T039: "Create frontend/lib/api/tasks.ts"
Task T040: "Create frontend/components/TaskForm.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup → ~30 minutes
2. Complete Phase 2: Foundational → ~2-3 hours
3. Complete Phase 3: User Story 1 → ~1-2 hours
4. **STOP and VALIDATE**: Test task creation independently
5. Deploy/demo if ready → MVP with single feature!

### Incremental Delivery

1. **Foundation** (Phases 1-2): Setup + Foundational → System ready for features
2. **MVP** (Phase 3): Add User Story 1 → Test independently → Deploy (create tasks!)
3. **v0.2** (Phase 4): Add User Story 2 → Test independently → Deploy (view tasks!)
4. **v0.3** (Phase 5): Add User Story 3 → Test independently → Deploy (edit tasks!)
5. **v0.4** (Phase 6): Add User Story 4 → Test independently → Deploy (delete tasks!)
6. **v1.0** (Phases 7-9): Add User Story 5 + Get Details + Polish → Full feature set!

Each increment adds value without breaking previous functionality.

### Parallel Team Strategy

With 3 developers after Phase 2 completes:

- **Developer A**: User Stories 1 + 2 (create + view) → Core flow
- **Developer B**: User Stories 3 + 4 (edit + delete) → Management features
- **Developer C**: User Story 5 + Get Details → Status tracking

All work in parallel, integrate at Phase 9.

---

## Task Summary

**Total Tasks**: 157

**Tasks by Phase**:
- Phase 1 (Setup): 5 tasks
- Phase 2 (Foundational): 26 tasks (CRITICAL - blocks all stories)
- Phase 3 (US1 - Create): 15 tasks
- Phase 4 (US2 - View): 20 tasks
- Phase 5 (US3 - Update): 20 tasks
- Phase 6 (US4 - Delete): 15 tasks
- Phase 7 (US5 - Complete): 15 tasks
- Phase 8 (Get Details): 11 tasks
- Phase 9 (Polish): 30 tasks

**Tasks by User Story**:
- US1 (Create Task): 15 tasks
- US2 (View List): 20 tasks
- US3 (Update Task): 20 tasks
- US4 (Delete Task): 15 tasks
- US5 (Toggle Complete): 15 tasks
- Supporting (Get Details): 11 tasks
- Infrastructure (Setup + Foundational): 31 tasks
- Polish: 30 tasks

**Parallel Opportunities**: 45+ tasks marked [P] can run in parallel

**Independent Test Criteria**: Each user story has clear test criteria for independent validation

**MVP Scope**: Phases 1-3 (User Story 1 only) → ~36 tasks → 4-6 hours

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Backend tests ensure quality and catch regressions
- Commit after each task or logical group of parallel tasks
- Stop at any checkpoint to validate story independently
- Use skills for code generation: fastapi-sqlmodel (backend), nextjs-betterauth (frontend), shadcn-ui-library (UI components)
