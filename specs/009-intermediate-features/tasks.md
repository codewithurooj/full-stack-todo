# Tasks: Intermediate Task Management Features

**Input**: Design documents from `/specs/009-intermediate-features/`
**Prerequisites**: plan.md (complete), spec.md (complete)

**Tests**: Tests are OPTIONAL per specification. This feature includes basic validation tests but not comprehensive TDD.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This is a full-stack web application with:
- **Backend**: `backend/app/` for source code, `backend/tests/` for tests
- **Frontend**: `frontend/app/` and `frontend/components/` for source code
- **Database**: `backend/migrations/` for SQL migrations

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and database migration setup

- [ ] T001 Create migration files directory if not exists at backend/migrations/
- [ ] T002 Create migration tracking mechanism (migration version table)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database schema changes that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Create forward migration SQL script at backend/migrations/002_add_priority_tags.sql
- [ ] T004 Create rollback migration SQL script at backend/migrations/002_add_priority_tags_rollback.sql
- [ ] T005 Test migration on local development database
- [ ] T006 Apply migration to development database
- [ ] T007 Verify priority column exists with default value 'medium'
- [ ] T008 Verify tags column exists with default empty array
- [ ] T009 Verify priority index idx_tasks_priority created successfully
- [ ] T010 Update Task model with priority field in backend/app/models/task.py
- [ ] T011 Update Task model with tags field in backend/app/models/task.py
- [ ] T012 Add priority validation (enum: high, medium, low) in backend/app/models/task.py
- [ ] T013 Add tags array type configuration in backend/app/models/task.py

**Checkpoint**: Foundation ready - database schema updated, models updated - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Task Prioritization (Priority: P1) 🎯 MVP

**Goal**: Users can assign priority levels (high/medium/low) to tasks with visual indicators, enabling basic task organization by importance

**Independent Test**: Create tasks with different priorities, verify priority is persisted in database, check visual indicators display correctly (high=red, medium=yellow, low=green), edit priority and confirm update, verify default priority is medium for new tasks

### Implementation for User Story 1

- [ ] T014 [P] [US1] Update TaskCreate schema to accept priority parameter in backend/app/routes/tasks.py
- [ ] T015 [P] [US1] Update TaskUpdate schema to accept priority parameter in backend/app/routes/tasks.py
- [ ] T016 [P] [US1] Update TaskRead schema to return priority field in backend/app/routes/tasks.py
- [ ] T017 [US1] Update POST /api/{user_id}/tasks endpoint to handle priority in backend/app/routes/tasks.py
- [ ] T018 [US1] Update PUT /api/{user_id}/tasks/{id} endpoint to handle priority updates in backend/app/routes/tasks.py
- [ ] T019 [US1] Update GET /api/{user_id}/tasks endpoint to return priority field in backend/app/routes/tasks.py
- [ ] T020 [P] [US1] Create PriorityBadge component at frontend/components/tasks/priority-badge.tsx
- [ ] T021 [P] [US1] Define priority color styles (high=red, medium=yellow, low=green) in frontend/components/tasks/priority-badge.tsx
- [ ] T022 [US1] Update TaskItem component to display PriorityBadge in frontend/components/tasks/task-item.tsx
- [ ] T023 [US1] Update Task TypeScript type to include priority field in frontend/types/task.ts
- [ ] T024 [US1] Add priority dropdown to create task form in frontend/app/tasks/page.tsx
- [ ] T025 [US1] Add priority dropdown to edit task form in frontend/app/tasks/page.tsx
- [ ] T026 [US1] Set default priority value to 'medium' in task forms in frontend/app/tasks/page.tsx
- [ ] T027 [US1] Test priority creation via API (POST with priority=high)
- [ ] T028 [US1] Test priority update via API (PUT updating priority)
- [ ] T029 [US1] Test priority display in frontend UI

**Checkpoint**: At this point, User Story 1 should be fully functional - users can create tasks with priority, edit priority, and see visual priority indicators

---

## Phase 4: User Story 2 - Task Categorization with Tags (Priority: P2)

**Goal**: Users can add multiple tags/categories to tasks for flexible organization across projects and contexts, with autocomplete suggestions

**Independent Test**: Add single tag to task, add multiple tags to task, verify tags persist and display correctly, test tag autocomplete suggestions from existing tags, edit tags (add/remove), verify tags saved in database as array

### Implementation for User Story 2

- [ ] T030 [P] [US2] Update TaskCreate schema to accept tags array parameter in backend/app/routes/tasks.py
- [ ] T031 [P] [US2] Update TaskUpdate schema to accept tags array parameter in backend/app/routes/tasks.py
- [ ] T032 [P] [US2] Update TaskRead schema to return tags array field in backend/app/routes/tasks.py
- [ ] T033 [US2] Update POST /api/{user_id}/tasks endpoint to handle tags array in backend/app/routes/tasks.py
- [ ] T034 [US2] Update PUT /api/{user_id}/tasks/{id} endpoint to handle tags updates in backend/app/routes/tasks.py
- [ ] T035 [US2] Create GET /api/{user_id}/tasks/tags endpoint for unique tags in backend/app/routes/tasks.py
- [ ] T036 [US2] Implement tags aggregation query (collect unique tags from all user tasks) in backend/app/routes/tasks.py
- [ ] T037 [P] [US2] Create TagInput component with autocomplete at frontend/components/tasks/tag-input.tsx
- [ ] T038 [P] [US2] Implement tag autocomplete filtering logic in frontend/components/tasks/tag-input.tsx
- [ ] T039 [P] [US2] Create TagList component for displaying task tags at frontend/components/tasks/tag-list.tsx
- [ ] T040 [US2] Update Task TypeScript type to include tags array field in frontend/types/task.ts
- [ ] T041 [US2] Add TagInput component to create task form in frontend/app/tasks/page.tsx
- [ ] T042 [US2] Add TagInput component to edit task form in frontend/app/tasks/page.tsx
- [ ] T043 [US2] Update TaskItem component to display TagList in frontend/components/tasks/task-item.tsx
- [ ] T044 [US2] Fetch available tags for autocomplete suggestions in frontend/app/tasks/page.tsx
- [ ] T045 [US2] Add debounce to tag autocomplete API calls (300ms) in frontend/components/tasks/tag-input.tsx
- [ ] T046 [US2] Test tag creation via API (POST with tags array)
- [ ] T047 [US2] Test tag updates via API (PUT updating tags)
- [ ] T048 [US2] Test GET /tasks/tags endpoint returns unique tags
- [ ] T049 [US2] Test tag autocomplete UI functionality

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can manage priorities and tags on tasks

---

## Phase 5: User Story 3 - Advanced Filtering (Priority: P3)

**Goal**: Users can filter tasks by multiple criteria (status, priority, tags, date range) to quickly find relevant task subsets, with result counts and clear filter indicators

**Independent Test**: Filter by priority only (show high priority tasks), filter by tags only (show 'work' tagged tasks), filter by status only (show completed), combine multiple filters (high priority + work tag + pending status), verify result counts accurate, clear filters and verify all tasks shown

### Implementation for User Story 3

- [ ] T050 [P] [US3] Create query builder helper at backend/app/utils/query_builder.py
- [ ] T051 [P] [US3] Implement priority filter logic in query builder at backend/app/utils/query_builder.py
- [ ] T052 [P] [US3] Implement tags filter logic using overlap operator in query builder at backend/app/utils/query_builder.py
- [ ] T053 [P] [US3] Implement status filter logic in query builder at backend/app/utils/query_builder.py
- [ ] T054 [P] [US3] Implement date range filter logic in query builder at backend/app/utils/query_builder.py
- [ ] T055 [US3] Update GET /api/{user_id}/tasks endpoint with filter query parameters (priority, tags, status, date_from, date_to) in backend/app/routes/tasks.py
- [ ] T056 [US3] Integrate query builder with GET /tasks endpoint in backend/app/routes/tasks.py
- [ ] T057 [US3] Add filters_applied echo to response body in backend/app/routes/tasks.py
- [ ] T058 [US3] Add task count to response body in backend/app/routes/tasks.py
- [ ] T059 [P] [US3] Create TaskFilters component at frontend/components/tasks/task-filters.tsx
- [ ] T060 [P] [US3] Add priority filter dropdown in TaskFilters component at frontend/components/tasks/task-filters.tsx
- [ ] T061 [P] [US3] Add tags filter multi-select in TaskFilters component at frontend/components/tasks/task-filters.tsx
- [ ] T062 [P] [US3] Add status filter dropdown in TaskFilters component at frontend/components/tasks/task-filters.tsx
- [ ] T063 [P] [US3] Add date range filter inputs in TaskFilters component at frontend/components/tasks/task-filters.tsx
- [ ] T064 [P] [US3] Add clear filters button in TaskFilters component at frontend/components/tasks/task-filters.tsx
- [ ] T065 [US3] Implement filter state management using URL query params in frontend/app/tasks/page.tsx
- [ ] T066 [US3] Update fetchTasks API call to include filter parameters in frontend/lib/api.ts
- [ ] T067 [US3] Display active filter indicators in UI in frontend/app/tasks/page.tsx
- [ ] T068 [US3] Display filtered task count in UI in frontend/app/tasks/page.tsx
- [ ] T069 [US3] Test priority filter (filter by high returns only high priority tasks)
- [ ] T070 [US3] Test tags filter (filter by 'work' returns only work-tagged tasks)
- [ ] T071 [US3] Test status filter (filter by completed returns only completed tasks)
- [ ] T072 [US3] Test combined filters (priority + tags + status together)
- [ ] T073 [US3] Test date range filter (tasks created between dates)
- [ ] T074 [US3] Test filter clearing functionality

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - users can prioritize, tag, and filter tasks

---

## Phase 6: User Story 4 - Keyword Search (Priority: P3)

**Goal**: Users can search for tasks by keywords in title or description using case-insensitive partial matching, with real-time results and match counts

**Independent Test**: Search for keyword in task title, search for keyword in task description, verify case-insensitive matching (search 'MEETING' finds 'meeting'), verify partial matching (search 'meet' finds 'meeting'), clear search and verify all tasks shown, verify search result count accurate

### Implementation for User Story 4

- [ ] T075 [P] [US4] Implement search logic using ILIKE operator in query builder at backend/app/utils/query_builder.py
- [ ] T076 [P] [US4] Add search across title and description (OR logic) in query builder at backend/app/utils/query_builder.py
- [ ] T077 [US4] Update GET /api/{user_id}/tasks endpoint with search query parameter in backend/app/routes/tasks.py
- [ ] T078 [US4] Integrate search logic with query builder in backend/app/routes/tasks.py
- [ ] T079 [P] [US4] Create SearchBar component at frontend/components/tasks/search-bar.tsx
- [ ] T080 [P] [US4] Implement debounced search input (300ms) in SearchBar component at frontend/components/tasks/search-bar.tsx
- [ ] T081 [P] [US4] Add search result count display in SearchBar component at frontend/components/tasks/search-bar.tsx
- [ ] T082 [US4] Add SearchBar component to tasks page at frontend/app/tasks/page.tsx
- [ ] T083 [US4] Implement search state management using URL query params in frontend/app/tasks/page.tsx
- [ ] T084 [US4] Update fetchTasks API call to include search parameter in frontend/lib/api.ts
- [ ] T085 [US4] Test search in title (keyword appears in task title)
- [ ] T086 [US4] Test search in description (keyword appears in task description)
- [ ] T087 [US4] Test case-insensitive search (uppercase keyword matches lowercase content)
- [ ] T088 [US4] Test partial word matching (partial keyword matches full word)
- [ ] T089 [US4] Test search combined with filters (search + priority filter)

**Checkpoint**: At this point, User Stories 1-4 should all work independently - users can prioritize, tag, filter, and search tasks

---

## Phase 7: User Story 5 - Flexible Sorting (Priority: P4)

**Goal**: Users can sort task list by different criteria (due date, priority, creation date, alphabetically) to view tasks in their preferred order, with sort maintained across filters

**Independent Test**: Sort by due date (earliest first, nulls last), sort by priority (high > medium > low), sort by creation date (newest first), sort alphabetically by title (A-Z), verify sort persists when filters applied, change sort order and verify update

### Implementation for User Story 5

- [ ] T090 [P] [US5] Implement priority sort with custom order (high=1, medium=2, low=3) in query builder at backend/app/utils/query_builder.py
- [ ] T091 [P] [US5] Implement due_date sort with NULLS LAST in query builder at backend/app/utils/query_builder.py
- [ ] T092 [P] [US5] Implement created_at sort (ascending/descending) in query builder at backend/app/utils/query_builder.py
- [ ] T093 [P] [US5] Implement title sort (alphabetical, case-insensitive) in query builder at backend/app/utils/query_builder.py
- [ ] T094 [US5] Update GET /api/{user_id}/tasks endpoint with sort_by and sort_order query parameters in backend/app/routes/tasks.py
- [ ] T095 [US5] Integrate sort logic with query builder in backend/app/routes/tasks.py
- [ ] T096 [P] [US5] Create SortDropdown component at frontend/components/tasks/sort-dropdown.tsx
- [ ] T097 [P] [US5] Add sort options (due_date, priority, created_at, title) in SortDropdown at frontend/components/tasks/sort-dropdown.tsx
- [ ] T098 [P] [US5] Add sort order toggle (asc/desc) in SortDropdown at frontend/components/tasks/sort-dropdown.tsx
- [ ] T099 [US5] Add SortDropdown component to tasks page at frontend/app/tasks/page.tsx
- [ ] T100 [US5] Implement sort state management using URL query params in frontend/app/tasks/page.tsx
- [ ] T101 [US5] Update fetchTasks API call to include sort parameters in frontend/lib/api.ts
- [ ] T102 [US5] Test sort by due_date (earliest first, tasks without due date at end)
- [ ] T103 [US5] Test sort by priority (high > medium > low order)
- [ ] T104 [US5] Test sort by created_at (newest first)
- [ ] T105 [US5] Test sort by title (alphabetical A-Z)
- [ ] T106 [US5] Test sort maintained when filters applied

**Checkpoint**: All user stories should now be independently functional - complete intermediate task management feature set

---

## Phase 8: AI Chatbot Integration (MCP Tools)

**Goal**: Update MCP tools to support priority and tags, enabling natural language task management through AI chatbot

**Independent Test**: Use chatbot to create high priority task, use chatbot to add task with tags, use chatbot to filter by priority, use chatbot to search tasks, use chatbot to sort tasks, verify 95% accuracy in interpreting priority/tag keywords

### Implementation for MCP Tools

- [ ] T107 [P] Update add_task MCP tool schema to accept priority parameter in backend/app/mcp_server/tools/add_task.py
- [ ] T108 [P] Update add_task MCP tool schema to accept tags array in backend/app/mcp_server/tools/add_task.py
- [ ] T109 [P] Update add_task MCP tool handler to process priority and tags in backend/app/mcp_server/tools/add_task.py
- [ ] T110 [P] Update list_tasks MCP tool schema to accept filter parameters (priority, tags, status, search) in backend/app/mcp_server/tools/list_tasks.py
- [ ] T111 [P] Update list_tasks MCP tool schema to accept sort parameters (sort_by, sort_order) in backend/app/mcp_server/tools/list_tasks.py
- [ ] T112 [P] Update list_tasks MCP tool handler to apply filters and sorting in backend/app/mcp_server/tools/list_tasks.py
- [ ] T113 [P] Update update_task MCP tool schema to accept priority parameter in backend/app/mcp_server/tools/update_task.py
- [ ] T114 [P] Update update_task MCP tool schema to accept tags array in backend/app/mcp_server/tools/update_task.py
- [ ] T115 [P] Update update_task MCP tool handler to process priority and tags in backend/app/mcp_server/tools/update_task.py
- [ ] T116 Add priority keyword mapping NLP (urgent/important → high, normal → medium, low/minor → low) in backend/app/mcp_server/tools/add_task.py
- [ ] T117 Add tag extraction NLP (parse 'with tags work and urgent') in backend/app/mcp_server/tools/add_task.py
- [ ] T118 Add filter intent recognition NLP (parse 'show high priority work tasks') in backend/app/mcp_server/tools/list_tasks.py
- [ ] T119 Test chatbot command: "add high priority task to call client"
- [ ] T120 Test chatbot command: "add task with tags work and urgent"
- [ ] T121 Test chatbot command: "show my high priority work tasks"
- [ ] T122 Test chatbot command: "find tasks about meeting"
- [ ] T123 Test chatbot command: "list tasks sorted by priority"
- [ ] T124 Test chatbot accuracy on 20 natural language commands (target 95% success)

**Checkpoint**: MCP tools fully updated - chatbot can manage priorities, tags, filters, search, and sorting through natural language

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T125 [P] Add validation for tag name format (alphanumeric, hyphens, underscores) in backend/app/models/task.py
- [ ] T126 [P] Add validation for max 50 tags per task in backend/app/models/task.py
- [ ] T127 [P] Add validation for max tag length 50 characters in backend/app/models/task.py
- [ ] T128 [P] Add error handling for invalid priority values in backend/app/routes/tasks.py
- [ ] T129 [P] Add error handling for invalid filter combinations in backend/app/routes/tasks.py
- [ ] T130 [P] Add logging for filter/search/sort operations in backend/app/routes/tasks.py
- [ ] T131 [P] Test performance: search response time < 1 second for 1000 tasks
- [ ] T132 [P] Test performance: filter response time < 1 second for 1000 tasks
- [ ] T133 [P] Test performance: sort response time < 500ms for 1000 tasks
- [ ] T134 [P] Test performance: tag autocomplete response < 200ms
- [ ] T135 [P] Update API documentation with new query parameters in specs/009-intermediate-features/contracts/tasks-api.md
- [ ] T136 [P] Update MCP tool documentation with priority/tags examples in backend/app/mcp_server/README.md
- [ ] T137 [P] Add examples to quickstart guide in specs/009-intermediate-features/quickstart.md
- [ ] T138 Test edge case: search with no matches returns empty array
- [ ] T139 Test edge case: filter with no matches returns empty array with count=0
- [ ] T140 Test edge case: duplicate tags on same task (should deduplicate)
- [ ] T141 Test edge case: very long tag name (should truncate or reject)
- [ ] T142 Test edge case: special characters in search query
- [ ] T143 Test edge case: contradictory filters (no results expected)
- [ ] T144 Test edge case: sort when all tasks have same priority
- [ ] T145 Verify all 41 functional requirements tested and passing
- [ ] T146 Verify all 25 acceptance scenarios validated
- [ ] T147 Run complete E2E test flow covering all 5 user stories
- [ ] T148 Code cleanup and remove any debug logging
- [ ] T149 Final deployment to staging environment
- [ ] T150 Validate against success criteria (performance metrics, usability)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on Foundational phase completion (independent from US1)
- **User Story 3 (Phase 5)**: Depends on Foundational phase completion (independent but benefits from US1/US2 data)
- **User Story 4 (Phase 6)**: Depends on Foundational phase completion (independent from other stories)
- **User Story 5 (Phase 7)**: Depends on Foundational phase completion (independent from other stories)
- **MCP Integration (Phase 8)**: Depends on US1 and US2 completion (needs priority and tags implemented)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent from US1, can run in parallel
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent but works best with US1/US2 data present
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Completely independent, can run in parallel
- **User Story 5 (P4)**: Can start after Foundational (Phase 2) - Independent but works best with US1 data (priority sorting)

### Within Each User Story

**User Story 1 (Priority)**:
- Backend schema updates (T014-T016) can run in parallel
- Backend endpoints (T017-T019) must run after schema updates
- Frontend components (T020-T021) can run in parallel with backend
- TaskItem update (T022) depends on PriorityBadge component (T020)
- Form updates (T024-T026) can run after TypeScript types updated (T023)

**User Story 2 (Tags)**:
- Backend schema updates (T030-T032) can run in parallel
- Backend endpoints (T033-T036) must run after schema updates
- Frontend components (T037-T039) can run in parallel with backend
- Form integration (T041-T043) depends on components being created

**User Story 3 (Filtering)**:
- Query builder functions (T050-T054) can run in parallel
- Backend endpoint (T055-T058) depends on query builder completion
- Frontend filter components (T059-T064) can run in parallel
- Filter state management (T065-T068) depends on components

**User Story 4 (Search)**:
- Backend search logic (T075-T076) can run in parallel
- Backend endpoint (T077-T078) depends on search logic
- Frontend SearchBar (T079-T081) can run in parallel with backend
- Integration (T082-T084) depends on SearchBar component

**User Story 5 (Sorting)**:
- All query builder sort functions (T090-T093) can run in parallel
- Backend endpoint (T094-T095) depends on sort logic
- Frontend SortDropdown (T096-T098) can run in parallel with backend
- Integration (T099-T101) depends on SortDropdown component

**MCP Integration (Phase 8)**:
- All schema updates (T107-T108, T110-T111, T113-T114) can run in parallel
- Handler updates depend on schema updates
- NLP enhancements (T116-T118) can run in parallel

### Parallel Opportunities

**Setup Phase**: T001-T002 can run sequentially (simple setup)

**Foundational Phase**: T003-T004 (migration files) can run in parallel, then T005-T013 run sequentially (need to test and apply migration)

**User Story 1**: T014-T016 in parallel, T020-T021 in parallel

**User Story 2**: T030-T032 in parallel, T037-T039 in parallel

**User Story 3**: T050-T054 in parallel, T059-T064 in parallel

**User Story 4**: T075-T076 in parallel, T079-T081 in parallel

**User Story 5**: T090-T093 in parallel, T096-T098 in parallel

**MCP Integration**: T107-T115 all parallelizable (different tool files)

**Polish Phase**: T125-T134 can run in parallel (different concerns)

---

## Parallel Example: User Story 1

```bash
# Launch backend schema updates together:
Task: "Update TaskCreate schema to accept priority parameter in backend/app/routes/tasks.py"
Task: "Update TaskUpdate schema to accept priority parameter in backend/app/routes/tasks.py"
Task: "Update TaskRead schema to return priority field in backend/app/routes/tasks.py"

# Launch frontend components together:
Task: "Create PriorityBadge component at frontend/components/tasks/priority-badge.tsx"
Task: "Define priority color styles in frontend/components/tasks/priority-badge.tsx"
```

## Parallel Example: User Story 3

```bash
# Launch all query builder filter functions together:
Task: "Implement priority filter logic in query builder at backend/app/utils/query_builder.py"
Task: "Implement tags filter logic using overlap operator in query builder at backend/app/utils/query_builder.py"
Task: "Implement status filter logic in query builder at backend/app/utils/query_builder.py"
Task: "Implement date range filter logic in query builder at backend/app/utils/query_builder.py"

# Launch all frontend filter UI components together:
Task: "Add priority filter dropdown in TaskFilters component"
Task: "Add tags filter multi-select in TaskFilters component"
Task: "Add status filter dropdown in TaskFilters component"
Task: "Add date range filter inputs in TaskFilters component"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003-T013) - CRITICAL: blocks all stories
3. Complete Phase 3: User Story 1 (T014-T029) - Priority feature only
4. **STOP and VALIDATE**: Test priority creation, update, display independently
5. Deploy/demo MVP with basic priority management

### Incremental Delivery

1. **Foundation**: Complete Setup + Foundational → Database ready
2. **Iteration 1 (MVP)**: Add US1 (Priority) → Test independently → Deploy
3. **Iteration 2**: Add US2 (Tags) → Test independently → Deploy
4. **Iteration 3**: Add US3 (Filtering) + US4 (Search) → Test independently → Deploy
5. **Iteration 4**: Add US5 (Sorting) → Test independently → Deploy
6. **Iteration 5**: Add MCP Integration → Test chatbot commands → Deploy
7. **Final**: Polish and validate all success criteria → Production deploy

Each iteration adds value without breaking previous functionality.

### Parallel Team Strategy

With multiple developers after Foundational phase completes:

**Sprint 1** (Foundation):
- All team: Complete Phase 1 + Phase 2 together

**Sprint 2** (Core Features):
- Developer A: User Story 1 (Priority - P1)
- Developer B: User Story 2 (Tags - P2)

**Sprint 3** (Discovery Features):
- Developer A: User Story 3 (Filtering - P3)
- Developer B: User Story 4 (Search - P3)
- Developer C: User Story 5 (Sorting - P4)

**Sprint 4** (Integration):
- Developer A: MCP Integration (Phase 8)
- Developer B: Polish and validation (Phase 9)

Stories complete and integrate independently, enabling continuous delivery.

---

## Notes

- **[P] tasks**: Different files, no dependencies - safe to parallelize
- **[Story] label**: Maps task to specific user story for traceability (US1=Priority, US2=Tags, US3=Filtering, US4=Search, US5=Sorting)
- **Each user story is independently testable**: Complete any story and verify it works without other stories
- **Database migration is foundational**: Must complete before ANY user story work begins
- **Performance targets**: Search <1s, Filter <1s, Sort <500ms for 1000 tasks
- **Chatbot integration**: Depends on US1 and US2 (needs priority and tags implemented first)
- **Total task count**: 150 tasks across 9 phases
- **Estimated effort**: 2-3 days (12-18 hours) for full implementation
- **Complexity**: Medium (database migration + full-stack updates + MCP integration)

Commit after each task or logical group. Stop at any checkpoint to validate story independently.

**Avoid**: Vague tasks, same-file conflicts, cross-story dependencies that break independence
