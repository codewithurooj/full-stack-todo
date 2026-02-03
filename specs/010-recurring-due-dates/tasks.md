# Tasks: Recurring Tasks and Due Dates with Reminders

**Feature**: 010-recurring-due-dates
**Spec**: [spec.md](spec.md)
**Plan**: [plan.md](plan.md)
**Branch**: `010-recurring-due-dates`
**Total Tasks**: 138 (organized across 7 implementation phases)

---

## Task Format Reference

- **[T###]** = Task ID (sequential within each phase)
- **[P]** = Parallelizable (can run independent of other tasks)
- **[US#]** = User Story (1-4, corresponding to priority P1-P4)
- Task description includes relative file path from project root

**Task Status Legend**:
- `[ ]` = Pending (not started)
- `[x]` = Completed
- `[>]` = In Progress

---

## Dependencies Between Phases

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational)
    ↓
Phase 3 (US1: Due Dates) ← Independent, can test solo
    ↓
Phase 4 (US2: Notifications) ← Depends on Phase 3
    ↓
Phase 5 (US3: Recurring) ← Depends on Phase 3
    ↓
Phase 6 (US4: Advanced Recurring) ← Depends on Phase 5
    ↓
Phase 7 (Polish & Integration)
```

**Parallel Execution**: Phase 3, 4, 5 can run in parallel after Phase 2 completes, but Phase 6 must wait for Phase 5. Phase 7 begins after Phase 3 is stable.

---

## Phase 1: Setup & Infrastructure

**Duration**: 1 day | **Blocking**: Yes (required before all other phases)

### Database Migration & Dependencies

- [x] [T001] [P] [US1] Create database migration script adding due_date column
  `backend/migrations/003_add_due_dates_reminders.sql`

- [x] [T002] [P] [US2] Create reminders table in migration script
  `backend/migrations/003_add_due_dates_reminders.sql` (add reminders table definition)

- [x] [T003] [P] [US1] Add indexes for due_date, parent_id, recurring_pattern for performance
  `backend/migrations/003_add_due_dates_reminders.sql` (add CREATE INDEX statements)

- [x] [T004] [US1] Update backend/requirements.txt with APScheduler, python-dateutil, pytz
  `backend/requirements.txt`

- [x] [T005] [US1] Update frontend/package.json with date-fns, date-fns-tz dependencies
  `frontend/package.json`

- [x] [T006] [P] [US1] Create environment variable documentation file
  `specs/010-recurring-due-dates/env-vars.md`

- [x] [T007] [US1] Apply database migration to development/test database
  Execute migration script locally (manual verification step)

---

## Phase 2: Foundational Backend Services

**Duration**: 1.5 days | **Blocking for all subsequent phases**

### Utilities & Base Infrastructure

- [x] [T008] [P] [US1] Create timezone utility module with pytz integration
  `backend/app/utils/timezone.py` (convert local ↔ UTC, DST handling)

- [x] [T009] [P] [US1] Create date parser utility for flexible date input
  `backend/app/utils/date_parser.py` (parse "tomorrow 9am", relative dates)

- [x] [T010] [P] [US3] Create RRULE wrapper utility for recurrence pattern generation
  `backend/app/utils/rrule.py` (dateutil.rrule wrapper, next_occurrence calculation)

- [x] [T011] [P] [US2] Create notification batching utility
  `backend/app/utils/notification.py` (batch reminders by time window, deduplication)

- [x] [T012] [US1] Create base models extension with SQLModel due_date support
  `backend/app/models/task.py` (extend Task: add due_date, recurring_pattern, parent_task_id fields)

- [x] [T013] [US2] Create Reminder model with SQLModel
  `backend/app/models/reminder.py` (new Reminder model with remind_at, delivery_status)

- [x] [T014] [P] [US1] Write unit tests for timezone conversion (UTC, EST, PST, DST)
  `backend/tests/test_timezone.py`

- [x] [T015] [P] [US3] Write unit tests for RRULE pattern generation
  `backend/tests/test_rrule.py`

- [x] [T016] [P] [US1] Write unit tests for date parser (flexible input formats)
  `backend/tests/test_date_parser.py`

---

## Phase 3: User Story 1 - Due Dates (P1: Foundation)

**Duration**: 1.5 days | **Dependencies**: Phase 1, 2 | **Independent test**: Yes

### Backend: Due Date API

- [x] [T017] [P] [US1] Create due date routes module
  `backend/app/routes/due_dates.py` (PUT/DELETE endpoints)

- [x] [T018] [US1] Implement PUT /api/{user_id}/tasks/{task_id}/due-date endpoint
  `backend/app/routes/due_dates.py` (set/update due date with timezone awareness)

- [x] [T019] [US1] Implement DELETE /api/{user_id}/tasks/{task_id}/due-date endpoint
  `backend/app/routes/due_dates.py` (remove due date, revert to unscheduled)

- [x] [T020] [P] [US1] Extend GET /api/{user_id}/tasks with due_date filtering
  `backend/app/routes/tasks.py` (add due_date_from, due_date_to query params)

- [x] [T021] [P] [US1] Implement relative date range filtering (today, this_week, overdue)
  `backend/app/routes/tasks.py` (add relative_range query param: today|this_week|this_month|overdue)

- [x] [T022] [US1] Implement GET /api/{user_id}/tasks?sort=due_date endpoint
  `backend/app/routes/tasks.py` (sorting by due date ascending/descending)

- [x] [T023] [P] [US1] Create task service extension for due date operations
  `backend/app/services/task_service.py` (update_task_due_date, clear_due_date helpers)

- [x] [T024] [P] [US1] Write tests for due date endpoints (CRUD operations)
  `backend/tests/test_due_dates.py` (test set, update, clear, filter, sort)

- [x] [T025] [P] [US1] Write tests for relative date range filtering (with timezone mocking)
  `backend/tests/test_due_dates.py` (test today, this_week, overdue with multiple timezones)

- [x] [T026] [US1] Write tests for due date persistence across requests
  `backend/tests/test_due_dates.py` (verify date stored and retrieved correctly)

### Frontend: Due Date UI

- [x] [T027] [P] [US1] Create DueDatePicker component with calendar UI
  `frontend/components/tasks/due-date-picker.tsx` (date + time selector with timezone support)

- [x] [T028] [P] [US1] Create DueDateEditor component for edit/clear functionality
  `frontend/components/tasks/due-date-editor.tsx` (inline edit, clear button)

- [x] [T029] [P] [US1] Create OverdueBadge component for visual indication
  `frontend/components/ui/overdue-badge.tsx` (red badge, "Overdue" text, relative time)

- [x] [T030] [P] [US1] Extend TaskItem component to display due date and overdue indicator
  `frontend/components/tasks/task-item.tsx` (show due date, apply overdue styling)

- [x] [T031] [P] [US1] Create DueDate filter component for task list filtering
  `frontend/components/tasks/due-date-filter.tsx` (today, this_week, overdue buttons)

- [x] [T032] [P] [US1] Create DueDateSort component for sorting options
  `frontend/components/tasks/sort-dropdown.tsx` (extend with due date sort options)

- [x] [T033] [P] [US1] Extend TaskForm component to include due date picker
  `frontend/components/tasks/task-form.tsx` or `create-task-form.tsx` (add due date field)

- [x] [T034] [P] [US1] Create useDueDate hook for state management
  `frontend/hooks/useDueDate.ts` (manage due date state, API calls)

- [x] [T035] [P] [US1] Create date-utils library for formatting and timezone conversion
  `frontend/lib/date-utils.ts` (format dates, parse user input, convert timezones)

- [x] [T036] [P] [US1] Create API client functions for due date operations
  `frontend/lib/api/due-dates.ts` (setDueDate, clearDueDate, filterByDueDate)

- [x] [T037] [P] [US1] Write tests for DueDatePicker component
  `frontend/__tests__/components/due-date-picker.test.tsx` (calendar interaction, selection)

- [x] [T038] [P] [US1] Write tests for due date filtering on task list
  `frontend/__tests__/components/task-list.test.tsx` (verify filters apply correctly)

- [x] [T039] [US1] Write E2E test for due date workflow (create → set due → filter → sort)
  `frontend/__tests__/e2e/due-dates.e2e.ts`

### MCP Tools: Due Date Support

- [x] [T040] [P] [US1] Extend add_task MCP tool to support due_date parameter
  `backend/app/mcp_server/tools/add_task.py` (add due_date field to schema)

- [x] [T041] [P] [US1] Extend update_task MCP tool to support due_date updates
  `backend/app/mcp_server/tools/update_task.py` (support updating due dates via AI)

- [x] [T042] [P] [US1] Write tests for MCP add_task with due_date
  `backend/tests/test_mcp_due_dates.py` (test AI commands like "add task due tomorrow")

---

## Phase 4: User Story 2 - Browser Notifications (P2: Reminders)

**Duration**: 2 days | **Dependencies**: Phase 1, 2, 3 | **Independent test**: Yes (after Phase 3)

### Backend: Reminder Scheduling

- [x] [T043] [P] [US2] Create reminders routes module
  `backend/app/routes/reminders.py` (POST/GET/DELETE/PATCH endpoints)

- [x] [T044] [US2] Implement POST /api/{user_id}/tasks/{task_id}/reminders endpoint
  `backend/app/routes/reminders.py` (create reminder with offset_minutes)

- [x] [T045] [US2] Implement GET /api/{user_id}/tasks/{task_id}/reminders endpoint
  `backend/app/routes/reminders.py` (list all reminders for a task)

- [x] [T046] [US2] Implement DELETE /api/{user_id}/tasks/{task_id}/reminders/{reminder_id} endpoint
  `backend/app/routes/reminders.py` (delete specific reminder)

- [x] [T047] [US2] Implement PATCH /api/{user_id}/tasks/{task_id}/reminders/{reminder_id}/snooze endpoint
  `backend/app/routes/reminders.py` (snooze reminder, reschedule for later)

- [x] [T048] [P] [US2] Create reminder service for scheduling and delivery
  `backend/app/services/reminder_service.py` (calculate remind_at, schedule with APScheduler)

- [x] [T049] [P] [US2] Create notification service for sending browser notifications
  `backend/app/services/notification_service.py` (format notifications, handle batching, delivery logging)

- [x] [T050] [P] [US2] Implement APScheduler configuration and job registry
  `backend/app/jobs/scheduler.py` (AsyncIOScheduler setup with PostgreSQL jobstore)

- [x] [T051] [US2] Create reminder processor job that triggers notifications at scheduled times
  `backend/app/jobs/reminder_processor.py` (runs every 30 seconds, processes due reminders)

- [x] [T052] [P] [US2] Implement notification deduplication logic
  `backend/app/services/notification_service.py` (prevent duplicate notifications within 5-min window)

- [x] [T053] [P] [US2] Implement notification batching for multiple reminders
  `backend/app/services/notification_service.py` (batch tasks due within 2-minute window)

- [x] [T054] [P] [US2] Create offline notification queue/persistence
  `backend/app/services/notification_service.py` (queue notifications for 24-hour window)

- [x] [T055] [P] [US2] Write tests for reminder creation and scheduling
  `backend/tests/test_reminders.py` (create reminder, verify remind_at calculated correctly)

- [x] [T056] [P] [US2] Write tests for notification batching and deduplication
  `backend/tests/test_reminders.py` (batch multiple reminders, prevent duplicates)

- [x] [T057] [P] [US2] Write tests for notification delivery with mocked time
  `backend/tests/test_reminders.py` (mock clock, verify notification triggers at correct time)

- [x] [T058] [US2] Write tests for offline notification queuing
  `backend/tests/test_reminders.py` (queue notifications, retrieve when reconnected)

### Frontend: Browser Notifications

- [x] [T059] [P] [US2] Create Service Worker for background notifications
  `frontend/public/service-worker.ts` (listen for push events, show notifications)

- [x] [T060] [P] [US2] Create notification service module for permission handling
  `frontend/lib/notification-service.ts` (request permission, register SW, check support)

- [x] [T061] [P] [US2] Create notification API client module
  `frontend/lib/api/reminders.ts` (createReminder, deleteReminder, listReminders, snoozeReminder)

- [x] [T062] [P] [US2] Create ReminderManager component for add/remove/snooze UI
  `frontend/components/tasks/reminder-manager.tsx` (modal/form to manage reminders)

- [x] [T063] [P] [US2] Create NotificationDisplay component to show delivered notifications
  `frontend/components/notifications/notification-display.tsx` (show notification history, click tracking)

- [x] [T064] [P] [US2] Extend TaskItem component to show reminder indicators
  `frontend/components/tasks/task-item.tsx` (badge showing number of reminders, upcoming reminder time)

- [x] [T065] [P] [US2] Create useReminders hook for reminder state management
  `frontend/hooks/useReminders.ts` (manage reminder list, add, delete, snooze)

- [x] [T066] [US2] Implement notification permission request flow
  `frontend/lib/notification-service.ts` (request permission on first reminder creation)

- [x] [T067] [P] [US2] Create fallback in-app alert component for denied permissions
  `frontend/components/notifications/in-app-alert.tsx` (show badge counter, in-app notifications)

- [x] [T068] [P] [US2] Implement offline notification persistence
  `frontend/lib/notification-service.ts` (persist queued notifications to localStorage)

- [x] [T069] [P] [US2] Write tests for Service Worker notification handling
  `frontend/__tests__/service-worker.test.ts` (mock push event, verify notification shown)

- [x] [T070] [P] [US2] Write tests for notification permission request flow
  `frontend/__tests__/lib/notification-service.test.ts` (test permission grant/deny)

- [x] [T071] [P] [US2] Write tests for ReminderManager component
  `frontend/__tests__/components/reminder-manager.test.tsx` (add, delete, snooze reminders)

- [x] [T072] [US2] Write E2E test for notification delivery workflow
  `frontend/__tests__/e2e/notifications.e2e.ts` (create task → add reminder → verify notification)

### MCP Tools: Reminder Support

- [x] [T073] [P] [US2] Create add_reminder MCP tool
  `backend/app/mcp_server/tools/add_reminder.py` (new tool to add reminders via AI)

- [x] [T074] [P] [US2] Create list_reminders MCP tool
  `backend/app/mcp_server/tools/list_reminders.py` (new tool to list task reminders via AI)

- [x] [T075] [P] [US2] Update MCP server to register new reminder tools
  `backend/app/mcp_server/server.py` (add add_reminder, list_reminders to tool registry)

- [x] [T076] [P] [US2] Write tests for MCP reminder tools
  `backend/tests/test_mcp_reminders.py` (test AI commands like "remind me in 15 minutes")

---

## Phase 5: User Story 3 - Recurring Tasks (P3: Auto-Generation)

**Duration**: 2 days | **Dependencies**: Phase 1, 2, 3 | **Independent test**: Yes (after Phase 3)

### Backend: Recurring Task Logic

- [x] [T077] [P] [US3] Extend Task model with recurring_pattern, recurring_end_date, parent_task_id fields
  `backend/app/models/task.py` (add recurring columns, update SQLModel definition)

- [x] [T078] [P] [US3] Create recurring task routes module
  `backend/app/routes/recurring.py` (PUT/DELETE/POST endpoints)

- [x] [T079] [US3] Implement PUT /api/{user_id}/tasks/{task_id}/recurring endpoint
  `backend/app/routes/recurring.py` (create/update recurring pattern with RRULE validation)

- [x] [T080] [US3] Implement DELETE /api/{user_id}/tasks/{task_id}/recurring endpoint
  `backend/app/routes/recurring.py` (remove recurring pattern with delete_type options)

- [x] [T081] [US3] Implement POST /api/{user_id}/tasks/{task_id}/next-occurrence endpoint
  `backend/app/routes/recurring.py` (calculate and return next occurrence date)

- [x] [T082] [P] [US3] Create recurring task service for instance generation
  `backend/app/services/recurring_service.py` (generate instances, backfill logic)

- [x] [T083] [P] [US3] Implement recurring instance generation with dateutil.rrule
  `backend/app/services/recurring_service.py` (create new Task instances based on pattern)

- [x] [T084] [US3] Implement backfill logic for missed recurring instances (up to 7 days)
  `backend/app/services/recurring_service.py` (backfill on user login or list request)

- [x] [T085] [P] [US3] Create recurring task generator job for background instance creation
  `backend/app/jobs/recurring_generator.py` (runs every 1 minute, generates instances)

- [x] [T086] [P] [US3] Implement task completion hook to prevent duplicate instances on next generation
  `backend/app/services/recurring_service.py` (update next_occurrence after instance creation)

- [x] [T087] [P] [US3] Write tests for recurring pattern creation (daily, weekly, monthly)
  `backend/tests/test_recurring.py` (create patterns, verify RRULE generated correctly)

- [x] [T088] [P] [US3] Write tests for recurring instance generation
  `backend/tests/test_recurring.py` (generate instances, verify dates match pattern)

- [x] [T089] [P] [US3] Write tests for backfill logic with various time windows
  `backend/tests/test_recurring.py` (backfill 1 day, 7 days, verify correct number of instances)

- [x] [T090] [US3] Write tests for next_occurrence calculation
  `backend/tests/test_recurring.py` (calculate next occurrence for various patterns)

### Frontend: Recurring Task UI

- [x] [T091] [P] [US3] Create RecurringTaskForm component for frequency selection
  `frontend/components/tasks/recurring-task-form.tsx` (daily, weekly, monthly selector)

- [x] [T092] [P] [US3] Create RecurrenceEditor component for advanced pattern configuration
  `frontend/components/tasks/recurrence-editor.tsx` (custom intervals, specific days, end date)

- [x] [T093] [P] [US3] Create RecurrenceDisplay component showing pattern in human-readable format
  `frontend/components/tasks/recurrence-display.tsx` ("Repeats Daily", "Repeats Weekly on Monday", etc)

- [x] [T094] [P] [US3] Extend TaskItem component to show recurring indicator
  `frontend/components/tasks/task-item.tsx` (badge/icon showing "Repeats [frequency]")

- [x] [T095] [P] [US3] Extend TaskForm to include recurring pattern selection
  `frontend/components/tasks/create-task-form.tsx` and `edit-task-form.tsx` (add recurring section)

- [x] [T096] [P] [US3] Create useRecurring hook for recurring task state management
  `frontend/hooks/useRecurring.ts` (manage recurring pattern, generate options)

- [x] [T097] [P] [US3] Create recurring API client module
  `frontend/lib/api/recurring.ts` (setRecurring, removeRecurring, getNextOccurrence)

- [x] [T098] [P] [US3] Create RRULE parser utility for displaying human-readable patterns
  `frontend/lib/rrule-parser.ts` (parse RRULE string to "Daily at 9 AM", etc)

- [x] [T099] [P] [US3] Write tests for RecurringTaskForm component
  `frontend/__tests__/components/recurring-task-form.test.tsx` (frequency selection, form submission)

- [x] [T100] [P] [US3] Write tests for RecurrenceDisplay component
  `frontend/__tests__/components/recurrence-display.test.tsx` (verify human-readable output)

- [x] [T101] [US3] Write E2E test for recurring task workflow
  `frontend/__tests__/e2e/recurring.e2e.ts` (create recurring → verify instances generated → complete instance)

### MCP Tools: Recurring Support

- [x] [T102] [P] [US3] Extend add_task MCP tool to support recurring_pattern parameter
  `backend/app/mcp_server/tools/add_task.py` (add recurring fields to schema)

- [x] [T103] [P] [US3] Extend update_task MCP tool to support recurring updates
  `backend/app/mcp_server/tools/update_task.py` (support updating recurring patterns)

- [x] [T104] [P] [US3] Write tests for MCP recurring commands
  `backend/tests/test_mcp_recurring.py` (test "create daily task", "make task weekly", etc)

---

## Phase 6: User Story 4 - Advanced Recurrence Patterns (P4: Power Users)

**Duration**: 1.5 days | **Dependencies**: Phase 1, 2, 3, 5 | **Independent test**: Yes (after Phase 5)

### Backend: Advanced Patterns

- [x] [T105] [P] [US4] Extend recurring service to support custom intervals (every N days/weeks)
  `backend/app/services/recurring_service.py` (update RRULE generation for INTERVAL)

- [x] [T106] [P] [US4] Implement monthly patterns with specific day-of-month selection
  `backend/app/services/recurring_service.py` (FREQ=MONTHLY;BYMONTHDAY=15, etc)

- [x] [T107] [P] [US4] Implement monthly patterns with last-day-of-month edge case handling
  `backend/app/services/recurring_service.py` (31st → 30th/28th/29th conversion)

- [x] [T108] [P] [US4] Implement weekly patterns with multiple specific days selection
  `backend/app/services/recurring_service.py` (FREQ=WEEKLY;BYDAY=MO,WE,FR, etc)

- [x] [T109] [P] [US4] Extend recurring routes with advanced pattern validation
  `backend/app/routes/recurring.py` (validate RRULE syntax, custom intervals)

- [x] [T110] [P] [US4] Write tests for custom interval patterns (every 2 weeks, every 3 days)
  `backend/tests/test_recurring.py` (verify correct instance spacing)

- [x] [T111] [P] [US4] Write tests for month-end edge cases (31st, February leap year)
  `backend/tests/test_recurring.py` (verify month-end handling)

- [x] [T112] [P] [US4] Write tests for multiple-day-of-week patterns
  `backend/tests/test_recurring.py` (verify instances on correct weekdays only)

### Frontend: Advanced Pattern UI

- [x] [T113] [P] [US4] Extend RecurrenceEditor to support custom interval selection
  `frontend/components/tasks/recurrence-editor.tsx` (every N days/weeks/months)

- [x] [T114] [P] [US4] Extend RecurrenceEditor to support specific weekday selection
  `frontend/components/tasks/recurrence-editor.tsx` (checkboxes for Mon-Sun)

- [x] [T115] [P] [US4] Extend RecurrenceEditor to support specific day-of-month selection
  `frontend/components/tasks/recurrence-editor.tsx` (number picker for 1-31)

- [x] [T116] [P] [US4] Add end-date picker to RecurrenceEditor
  `frontend/components/tasks/recurrence-editor.tsx` (UNTIL date selector)

- [x] [T117] [P] [US4] Create NextOccurrencePreview component showing upcoming instances
  `frontend/components/tasks/next-occurrence-preview.tsx` (list of next 5-10 occurrences)

- [x] [T118] [P] [US4] Write tests for advanced RecurrenceEditor patterns
  `frontend/__tests__/components/recurrence-editor.test.tsx` (custom intervals, weekday selection)

- [x] [T119] [US4] Write E2E test for advanced recurring patterns
  `frontend/__tests__/e2e/advanced-recurring.e2e.ts` (create pattern with custom interval, verify instances)

---

## Phase 7: Polish, Integration & Cross-Cutting

**Duration**: 1.5 days | **Dependencies**: All previous phases | **Testing focus**: Integration

### Performance & Optimization

- [x] [T120] [P] Add database indexes for due_date queries performance
  `backend/app/models/task.py` or migration script (verify indexes exist: due_date, remind_at, parent_task_id)

- [x] [T121] [P] Optimize recurring instance generation with batch inserts
  `backend/app/services/recurring_service.py` (use bulk_insert for multiple instances)

- [x] [T122] [P] Implement caching for frequently-accessed RRULE patterns
  `backend/app/services/recurring_service.py` (cache next_occurrence calculations)

- [x] [T123] [P] Optimize due date filtering with efficient query construction
  `backend/app/routes/tasks.py` (verify query plans, use indexes effectively)

### Error Handling & Edge Cases

- [x] [T124] [P] Implement timezone fallback when user timezone unavailable
  `backend/app/services/task_service.py` (use server timezone as fallback)

- [x] [T125] [P] Handle invalid RRULE patterns with helpful error messages
  `backend/app/routes/recurring.py` (catch dateutil exceptions, provide clear error)

- [x] [T126] [P] Handle browser notification permission denial gracefully
  `frontend/lib/notification-service.ts` (fallback to in-app alerts)

- [x] [T127] [P] Handle Service Worker registration failure
  `frontend/lib/notification-service.ts` (fallback to polling if unavailable)

- [x] [T128] [P] Implement retry logic for failed notification delivery
  `backend/app/services/notification_service.py` (retry failed notifications, track failures)

### Documentation & DevOps

- [x] [T129] [P] Create feature documentation in README.md
  `README.md` (add section for due dates, reminders, recurring tasks)

- [x] [T130] [P] Create troubleshooting guide for common issues
  `specs/010-recurring-due-dates/TROUBLESHOOTING.md` (reminders not firing, timezone issues, etc)

- [x] [T131] [P] Document MCP tool usage with examples
  `specs/010-recurring-due-dates/MCP-TOOLS.md` (example AI commands)

- [x] [T132] [P] Create API documentation file with examples
  `specs/010-recurring-due-dates/API.md` (copy of OpenAPI spec with cURL examples)

- [x] [T133] [P] Update docker-compose.yml with scheduler environment variables
  `docker-compose.yml` (add APSCHEDULER_TIMEZONE, NOTIFICATION_QUEUE_TTL)

### Integration Tests

- [x] [T134] Write end-to-end test: create task → set due date → add reminder → receive notification
  `backend/tests/e2e_test_due_dates_reminders.py` or `frontend/__tests__/e2e/full-workflow.e2e.ts`

- [x] [T135] Write end-to-end test: create recurring task → verify instances auto-generate → complete instance → verify template active
  `frontend/__tests__/e2e/recurring-workflow.e2e.ts`

- [x] [T136] Write load test: create 1000 tasks with due dates, verify filtering completes in <1s
  `backend/tests/load_test_due_dates.py` (pytest-benchmark or similar)

- [x] [T137] Write integration test: timezone change scenario
  `backend/tests/test_timezone_integration.py` (set due date, change timezone, verify display correct)

- [x] [T138] Verify all user stories independently testable: US1 only, US1+2, US1+3, US1+2+3+4
  Manual verification step (test each combination in isolated environment)

---

## Testing & Quality Checklist

### Unit Testing (Per Phase)

- **Phase 2**: All timezone, date parser, RRULE utilities tested with >90% coverage
- **Phase 3**: Due date CRUD operations tested; filtering/sorting verified
- **Phase 4**: Reminder creation, batching, deduplication tested; Service Worker mock tests
- **Phase 5**: Recurring pattern generation, backfill, next_occurrence tested
- **Phase 6**: Advanced patterns (custom intervals, month-end, weekday) tested
- **Phase 7**: Integration tests, load tests, edge case tests

### Frontend Testing

- DueDatePicker calendar interaction and selection
- Timezone conversion in date display
- Reminder manager add/remove/snooze flows
- Service Worker notification delivery
- RecurringTaskForm and advanced pattern selection
- E2E workflows: create → modify → verify

### Backend Testing

- All new endpoints (POST, PUT, DELETE, GET) with auth verification
- Due date calculations with timezone mocking
- Reminder scheduling with mocked clock
- Recurring instance generation with various patterns
- Batch notification and deduplication logic
- Database migration and rollback
- APScheduler job persistence and execution

### Manual Testing Checklist

- [ ] Create task with due date in user's timezone
- [ ] Edit due date to new value, verify reminders updated
- [ ] Create recurring task (daily), verify instances appear
- [ ] Complete one recurring instance, verify template generates more
- [ ] Set reminder, verify notification appears at correct time
- [ ] Close app before reminder fires, reopen, verify notification still appears
- [ ] Change device timezone, verify due dates display in new timezone
- [ ] Test with notification permission denied, verify in-app fallback works
- [ ] Create task with past due date, verify "Overdue" indicator appears
- [ ] Backfill test: stop generating instances (disable job), return after 8 days, verify backfill up to 7 days
- [ ] Test recurring pattern with month-end (31st), verify February handling
- [ ] Test batch notifications: create 5 tasks due within 2 minutes, verify single notification

---

## Task Dependencies Map

```
Phase 1: Setup
├─ T001-T003: Database migration
├─ T004-T005: Dependency updates
└─ T006-T007: Environment setup

Phase 2: Foundational
├─ T008-T011: Utilities (parallel)
├─ T012-T013: Models (depends on utilities)
└─ T014-T016: Unit tests (depends on utilities)

Phase 3: Due Dates [Independent after Phase 2]
├─ T017-T026: Backend endpoints & tests (parallel)
├─ T027-T039: Frontend UI & tests (parallel, depends on backend complete)
└─ T040-T042: MCP tools (depends on backend endpoints)

Phase 4: Notifications [Can start after Phase 3 backend complete]
├─ T043-T058: Backend reminders & tests (parallel)
├─ T059-T072: Frontend notifications (parallel, depends on backend complete)
└─ T073-T076: MCP tools (depends on backend endpoints)

Phase 5: Recurring [Can start after Phase 3 backend complete]
├─ T077-T090: Backend recurring (parallel)
├─ T091-T101: Frontend recurring (parallel, depends on backend complete)
└─ T102-T104: MCP tools (depends on backend endpoints)

Phase 6: Advanced Recurring [Requires Phase 5 complete]
├─ T105-T112: Backend advanced patterns (parallel)
├─ T113-T119: Frontend advanced UI (parallel, depends on backend)

Phase 7: Polish [All previous phases complete]
├─ T120-T123: Performance (parallel)
├─ T124-T128: Error handling (parallel)
├─ T129-T133: Documentation (parallel)
└─ T134-T138: Integration tests (sequential or parallel)
```

---

## Parallel Execution Roadmap

**Recommended Parallel Schedule** (assuming 2-3 person team):

1. **Phase 1**: 1 person (1 day) - Blocking setup
2. **Phase 2**: 1 person (1.5 days) - Blocking foundational

3. **Phases 3, 4, 5 in parallel** (2-3 days):
   - **Person A**: Phase 3 backend (T017-T026) + frontend (T027-T039)
   - **Person B**: Phase 4 backend (T043-T058) + frontend (T059-T072)
   - **Person C**: Phase 5 backend (T077-T090) + frontend (T091-T101)

4. **Phase 6** (1.5 days): 1-2 people (depends on Phase 5 complete)

5. **Phase 7** (1.5 days): Full team integration, testing, docs

**Total Duration**: ~9-10 days for full feature (optimized with parallelization)

---

## Success Metrics

- All 138 tasks completed
- All unit tests passing (>90% code coverage)
- All E2E tests passing
- Load test: 1000 tasks filtered by due date in <1s
- Performance test: Reminder notification delivered within 5 seconds of scheduled time
- All 4 user stories independently testable and working
- Zero critical bugs from manual testing checklist
- API contracts match spec exactly
- Documentation complete and examples working

---

## Notes for Implementation

1. **Task Ordering**: Phase 3-5-4 can be reordered (Phase 4 and 5 both depend on Phase 3 backend, but Phase 5 doesn't need Phase 4). Recommended: 3 → 5 → 4 → 6 to get recurring working early.

2. **Testing Strategy**: Each phase should have full test coverage before moving to next phase. Phase 7 validates integration across all phases.

3. **Database Migrations**: Must be applied before any code execution. Test migrations on dev/staging before production.

4. **Timezone Handling**: Use UTC for all storage, convert to user timezone on retrieval. Test thoroughly with multiple timezone scenarios.

5. **Job Scheduler**: APScheduler starts with app. Verify in startup logs before testing reminder functionality.

6. **Service Worker**: Requires HTTPS in production. Test locally with HTTP for development.

7. **API Testing**: Use provided API contracts for validation. Each endpoint should be tested for:
   - Happy path (valid input)
   - Error cases (invalid input, auth failures, not found)
   - Timezone handling (if applicable)
   - User isolation (no cross-user data leakage)

---

**Generated**: 2026-01-09
**Feature Branch**: `010-recurring-due-dates`
**Ready for Implementation**: Yes
