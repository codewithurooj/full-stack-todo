# Feature Specification: Recurring Tasks and Due Dates with Reminders

**Feature Branch**: `010-recurring-due-dates`
**Created**: 2026-01-08
**Status**: Draft
**Input**: "Create specification for advanced task features: recurring tasks (daily/weekly/monthly with auto-creation) and due dates with time-based reminders using browser notifications"

## User Scenarios & Testing

### User Story 1 - Set Due Dates for Tasks (Priority: P1)

As a task manager, I need to assign due dates and times to my tasks so that I can track deadlines and prioritize my work effectively. Users should be able to set, edit, and clear due dates with timezone awareness.

**Why this priority**: Due dates are foundational for task management. Without deadline tracking, users cannot prioritize effectively or receive timely reminders. This is the core requirement that enables all downstream reminder and recurring functionality.

**Independent Test**: Can be fully tested by creating tasks with due dates, filtering by due date, and sorting by deadline. Delivers the ability to manage task deadlines independently.

**Acceptance Scenarios**:

1. **Given** a user viewing the task list, **When** they click "Add due date" on a task and select a date/time, **Then** the task displays the due date and is sortable by deadline
2. **Given** a task with a due date, **When** the user edits the due date to a new value, **Then** the updated date is saved and reflected immediately
3. **Given** a task with a due date in the past, **When** the task is displayed, **Then** it shows an "Overdue" indicator in red
4. **Given** a user with multiple tasks with due dates, **When** they filter by "This Week", **Then** only tasks due within 7 days are shown
5. **Given** a task with a due date, **When** the user clicks "Clear due date", **Then** the due date is removed and the task returns to unscheduled state

---

### User Story 2 - Receive Browser Notifications for Due Tasks (Priority: P2)

As a task manager, I need to receive browser notifications when tasks are approaching their due dates so that I don't miss important deadlines. Notifications should be customizable per task with configurable advance notice times.

**Why this priority**: Reminders turn due dates from passive information into actionable alerts. This enables users to actually act on their deadlines rather than discovering missed deadlines after the fact.

**Independent Test**: Can be fully tested by setting reminders on tasks, granting browser notification permissions, and verifying notifications appear at scheduled times. Delivers the ability to stay on top of deadlines without constant manual checking.

**Acceptance Scenarios**:

1. **Given** a task with a due date set, **When** the user selects "Add reminder" and chooses "15 minutes before", **Then** a reminder is created and will trigger 15 minutes before the due time
2. **Given** a browser with notifications permission granted, **When** a reminder triggers at its scheduled time, **Then** a desktop notification appears showing the task title and due time
3. **Given** a user without notification permissions, **When** they attempt to add a reminder, **Then** the system requests permission before allowing reminder creation
4. **Given** a notification displayed to the user, **When** they click on it, **Then** the browser navigates to the specific task in the application
5. **Given** a task with multiple reminders, **When** the task is displayed, **Then** all reminders are listed and can be individually deleted
6. **Given** the browser is closed before a reminder triggers, **When** the reminder time arrives and the user reopens the app, **Then** a notification still appears or a dismissible alert shows the missed deadline

---

### User Story 3 - Create Recurring Tasks with Auto-Generation (Priority: P3)

As a task manager with routine work, I need to create recurring tasks that automatically generate new instances on a schedule (daily, weekly, monthly) so that I don't have to manually recreate repetitive tasks.

**Why this priority**: Recurring tasks eliminate manual work for routine tasks, but require more infrastructure than basic due dates. This is valuable for power users with regular workflows but can be deferred from basic MVP.

**Independent Test**: Can be fully tested by creating a recurring task with a specific frequency, waiting or simulating time passing, and verifying new instances are created automatically. Delivers the ability to manage routine work without manual recreation.

**Acceptance Scenarios**:

1. **Given** a user creating a new task, **When** they toggle "Make this recurring" and select "Weekly on Mondays", **Then** the task is created as a recurring template and the first instance is created for the upcoming Monday
2. **Given** a recurring task with daily frequency, **When** a day passes and the user returns to their task list, **Then** a new instance of that task automatically appears for the current day
3. **Given** a recurring task, **When** the user completes an instance, **Then** the instance is marked complete but the recurring template remains active to generate future instances
4. **Given** a recurring task template, **When** the user views the task details, **Then** they can see it's marked as recurring with the frequency (e.g., "Repeats weekly on Monday")
5. **Given** a recurring task that hasn't been checked in 7 days, **When** the user returns to their list, **Then** up to 7 previous instances are backfilled (not future instances, to avoid overwhelming the list)

---

### User Story 4 - Manage Recurrence Patterns (Priority: P4)

As an advanced task manager with complex recurring work, I need to configure advanced recurrence patterns (custom intervals, specific days of the week, monthly dates, end dates) so that my recurring tasks match my actual work schedule.

**Why this priority**: Advanced patterns handle edge cases like "every 2 weeks", "the last Friday of each month", or "repeat until a specific date". These are valuable but less critical than basic daily/weekly/monthly functionality.

**Independent Test**: Can be fully tested by creating recurring tasks with various advanced patterns and verifying correct instance generation. Delivers power-user features for complex schedules.

**Acceptance Scenarios**:

1. **Given** a user creating a recurring task, **When** they select "Custom" frequency and specify "every 2 weeks", **Then** instances are generated at 2-week intervals
2. **Given** a recurring task with "Monthly on the 31st", **When** a month has only 30 days, **Then** the instance is created on the last day of that month (30th)
3. **Given** a user configuring a recurring task, **When** they select "Repeat until: March 31, 2026", **Then** no instances are created after that date
4. **Given** a recurring task, **When** the user edits the recurrence pattern and saves, **Then** future instances are regenerated based on the new pattern
5. **Given** a recurring task with specific days selected (Mon, Wed, Fri), **When** instances should be generated, **Then** they only appear on those selected days

---

### Edge Cases

- **Timezone Changes**: When a user's device timezone changes, due dates and reminder times must be adjusted to maintain the correct absolute time. A task due at "9 AM EST" remains due at the same moment when timezone changes to PST (6 AM).
- **Missed Recurrences**: If a user doesn't open their app for 7 days, recurring task instances are backfilled for up to the last 7 days, but future instances are not pre-generated to avoid overwhelming the user.
- **Notification Permission Denial**: When users deny browser notification permissions, reminders still function internally with in-app alerts/badges, and users can re-enable permissions later.
- **Browser Closure Before Reminder**: If the browser closes before a reminder fires, the notification must be queued and delivered when the user reopens the app within a reasonable window (24 hours).
- **Past Due Dates**: Tasks with due dates in the past are clearly marked as "Overdue" and remain visible until manually cleared or completed.
- **Recurring on 31st**: For months with fewer than 31 days, the recurrence generates instances on the last day of the month.
- **Editing Recurring Instance vs Template**: When a user edits a single instance of a recurring task, changes apply only to that instance; editing the template updates all future instances.
- **Notification Spam Prevention**: Reminders are batched and deduplicated; if 5 tasks are due at the same time, only 1 combined notification is sent listing all 5 tasks.
- **Deletion of Recurring Templates**: When a recurring template is deleted, users are prompted whether to delete only future instances or all instances including past ones.
- **Recurrence Creation During Night**: A recurring task created at 11 PM for "daily at 9 AM" ensures the first reminder is triggered at 9 AM the next day, not immediately.

## Requirements

### Functional Requirements

**Due Date Management (FR-001 to FR-010)**

- **FR-001**: System MUST allow users to set a due date (date + time) on any task in their personal task list
- **FR-002**: System MUST store due dates with timezone information to handle user location changes accurately
- **FR-003**: System MUST allow users to clear/remove a due date from a task, reverting it to unscheduled status
- **FR-004**: System MUST display due dates in the user's local timezone
- **FR-005**: System MUST visually indicate tasks with due dates in the past as "Overdue" with a red indicator
- **FR-006**: System MUST support sorting tasks by due date (ascending: nearest first, descending: furthest first)
- **FR-007**: System MUST support filtering tasks by relative time ranges (Today, This Week, This Month, Overdue, Unscheduled)
- **FR-008**: System MUST update the visual "Overdue" status in real-time without requiring page refresh as time passes
- **FR-009**: System MUST allow editing a task's due date after creation, updating all associated reminders accordingly
- **FR-010**: System MUST persist due date information consistently across all views and devices for the same user

**Reminder Notifications (FR-011 to FR-025)**

- **FR-011**: System MUST allow users to set multiple reminders per task with configurable offset times (e.g., 5 min, 15 min, 1 hour, 1 day before due date)
- **FR-012**: System MUST request and validate browser notification permissions before enabling reminder functionality
- **FR-013**: System MUST deliver browser desktop notifications at the scheduled reminder time with task title and due time displayed
- **FR-014**: System MUST include a clickable link in notifications that opens the task detail when clicked
- **FR-015**: System MUST persist and queue notifications that should fire while the browser is closed, delivering them when the app reopens (within 24-hour window)
- **FR-016**: System MUST enable notifications even when the app tab is not active
- **FR-017**: System MUST batch multiple reminders scheduled within 2 minutes into a single notification listing all due tasks
- **FR-018**: System MUST store reminder metadata for auditing and re-triggering
- **FR-019**: System MUST allow users to delete individual reminders from a task without affecting other reminders
- **FR-020**: System MUST gracefully handle cases where browser notification permissions are denied by falling back to in-app alerts
- **FR-021**: System MUST prevent duplicate notifications from being sent for the same task/reminder pair within a 5-minute window
- **FR-022**: System MUST allow users to enable/disable notifications globally, and per-task
- **FR-023**: System MUST support sound and/or visual notification indicators per user preference
- **FR-024**: System MUST track notification delivery status (scheduled, sent, clicked, dismissed) for analytics
- **FR-025**: System MUST allow users to snooze notifications, re-triggering them after a selected duration (5 min, 15 min, 1 hour, 1 day)

**Recurring Task Management (FR-026 to FR-037)**

- **FR-026**: System MUST allow users to create a task as recurring with predefined frequencies: Daily, Weekly, Monthly
- **FR-027**: System MUST automatically generate new instances of recurring tasks at the specified frequency
- **FR-028**: System MUST maintain a recurring task template that contains the base task data (title, description, tags, frequency details)
- **FR-029**: System MUST create the first instance of a recurring task at creation time and schedule subsequent instances accordingly
- **FR-030**: System MUST backfill up to 7 days of missed recurring instances when a user returns after an absence (not future instances)
- **FR-031**: System MUST allow users to mark a single instance of a recurring task as complete without affecting other instances
- **FR-032**: System MUST allow users to mark all future instances of a recurring task as complete
- **FR-033**: System MUST generate recurring instances with due times matching the template's specified time of day (e.g., "9 AM" for daily recurring tasks)
- **FR-034**: System MUST display recurring tasks with a visible indicator (e.g., "Repeats Daily", "Repeats Weekly on Monday") in the UI
- **FR-035**: System MUST limit automatic backfill of recurring instances to 7 days to prevent overwhelming users with missed tasks
- **FR-036**: System MUST allow users to edit the recurring template, updating all future instances (not past ones)
- **FR-037**: System MUST allow users to delete a recurring template with an option to delete only future instances or all instances

**Advanced Recurrence Patterns (FR-038 to FR-044)**

- **FR-038**: System MUST support custom intervals for recurring tasks (e.g., "every 2 weeks", "every 3 days")
- **FR-039**: System MUST support recurring tasks based on specific days of the week (e.g., "Monday, Wednesday, Friday")
- **FR-040**: System MUST support recurring tasks with a specific day of month (e.g., "15th of each month")
- **FR-041**: System MUST handle months with different day counts (e.g., recurring on 31st rolls to last day of months with 30 days)
- **FR-042**: System MUST support setting an end date for recurring tasks; no instances created after the end date
- **FR-043**: System MUST support "next occurrence" calculation that determines when the next instance should be created based on the pattern
- **FR-044**: System MUST allow users to specify the recurrence start time (e.g., "Daily at 9 AM" or "Weekly on Monday at 2 PM")

### Key Entities

- **Task**: Represents a user's work item or to-do. Each task now includes optional due date/time information (when the task should be completed), associated reminders (advance notifications before due date), and a link to its recurring pattern if it was auto-generated.

- **Recurring Pattern**: Represents a repeating schedule for tasks. Defines how often tasks repeat (daily, weekly, monthly, or custom intervals), which days of the week or month, what time of day new instances should appear, when the pattern starts and ends, and the template information (title, description, tags) to use for each new instance.

- **Reminder**: Represents a scheduled notification for a task. Each reminder tracks when it should trigger (e.g., "15 minutes before due time"), whether it has been sent yet, and which task it belongs to.

- **Notification**: Represents a delivered or pending notification to the user. Tracks what task it's about, when it was or should be sent, whether the user has seen or clicked it, and preserves task details at the time of notification for context.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can set a due date on a task in less than 10 seconds using the UI
- **SC-002**: Users can create a recurring task with a predefined frequency in less than 30 seconds
- **SC-003**: Browser notifications are delivered within 5 seconds of the scheduled reminder time
- **SC-004**: Reminder notifications have a 99% delivery reliability rate (with offline queueing handling)
- **SC-005**: Recurring task instances are created automatically within 1 minute of the scheduled generation time
- **SC-006**: System handles 1,000+ active recurring tasks per user without performance degradation
- **SC-007**: Users can view all tasks with due dates in the next 30 days and sort/filter them in less than 1 second
- **SC-008**: Timezone changes are reflected in due date and reminder displays within 10 seconds of device timezone update
- **SC-009**: Setup of first due date and reminder is completed successfully by 90% of users without support intervention
- **SC-010**: 70% of users click through received reminder notifications to view their tasks
- **SC-011**: Recurring task instances are backfilled for users returning after 7+ days within 30 seconds of app load
- **SC-012**: 95% of recurring task instances are created on the correct day/time according to their pattern

## Assumptions

1. **Browser Notification Support**: Users have modern browsers that support desktop notifications and background notification delivery
2. **User Authentication**: Feature requires user authentication and operates within user-specific task namespaces; no shared/public tasks
3. **Timezone Awareness**: System can accurately handle timezone conversions for users in different geographic locations
4. **Consistent Time Representation**: System stores and displays times consistently, accounting for user timezone changes
5. **Background Time Calculation**: Reminder times and recurring generation times are calculated using the user's configured timezone
6. **Background Notification Capability**: System supports delivering notifications when the user is not actively viewing the application
7. **Automated Job Processing**: System can automatically perform scheduled tasks like generating recurring instances and triggering reminders
8. **Clock Synchronization**: User devices maintain reasonably synchronized clocks; extreme clock drift is out of scope
9. **Client-Side Data Persistence**: User's browser can persistently store notification preferences and pending alerts
10. **Notification Queuing**: System can queue and retry failed notification deliveries
11. **Permission-Based Notifications**: Browser follows standard permission model where users grant/deny notification access

## Dependencies

- **Feature 009 (Intermediate Tasks)**: Assumes existing task model, user authentication, and basic task CRUD operations
- **Background Job Processing**: Requires automated background job processing capability for:
  - Generating recurring task instances on schedule
  - Processing reminder queues and triggering notifications
  - Backfilling missed instances
- **Browser Background Notifications**: Requires browser support for delivering notifications when the app is not actively open
- **Desktop Notification Support**: Relies on browser notification capabilities for desktop alerts
- **Timezone-Aware Data Storage**: Data storage must preserve timezone information for accurate deadline tracking across time zones
- **Task Data Model**: Assumes existing task structure can accommodate due dates, reminders, and recurring pattern associations
- **User Preference Storage**: Assumes user settings can store notification preferences and timezone information

## Out of Scope

1. **Email and SMS Notifications**: Only browser notifications are implemented; email or SMS alerts are not included
2. **Calendar Sync**: Syncing to external calendars (Google Calendar, Outlook) is not supported
3. **Task Sharing and Collaboration**: Due dates and reminders apply to personal tasks only; shared task deadlines are out of scope
4. **AI-Powered Suggestions**: No automatic due date suggestions based on task title or content
5. **Snooze with Smart Rescheduling**: Basic snooze is supported, but intelligent rescheduling (e.g., "reschedule to tomorrow at the best time") is out of scope
6. **Recurring Task Exceptions**: Cannot mark specific instances of recurring tasks as exceptions; only individual instance completion/editing
7. **Complex RRULE Support**: iCalendar RRULE standard is not fully implemented; only simple patterns (daily, weekly, monthly, custom intervals)
8. **Completion-Based Recurrence**: Recurring tasks that generate next instance based on completion time (e.g., "7 days after completion") are not supported

## Notes

1. **Performance Considerations**: Recurring task generation should be done asynchronously via background jobs to avoid blocking user requests. Listing tasks with many recurring instances requires efficient pagination.

2. **Notification Reliability**: Missed notifications (browser closed) should be persisted and delivered when app reopens within 24 hours. Beyond 24 hours, notifications can be discarded to avoid notification spam on stale tasks.

3. **User Experience**: Due date indicators should be visual and prominent (color, badge, icon) to aid quick scanning of task lists. Overdue tasks should stand out clearly in red.

4. **Data Retention**: Completed recurring task instances should be retained for audit purposes for at least 90 days before archival/deletion. Notification delivery logs should be retained for 30 days for troubleshooting.

5. **Testing Strategy**: Thorough testing required for:
   - Timezone conversion and edge cases (DST transitions, timezone database updates)
   - Recurring task generation under high load
   - Notification delivery with service worker active/inactive
   - Backfill logic with various time ranges
   - Browser notification permission grant/denial flows

6. **Mobile Considerations**: Browser notifications work differently on mobile (may not show as desktop notifications). Consider in-app badge/alert as primary notification method on mobile, with push notifications as secondary if supported.

7. **Accessibility**: All due date pickers must be keyboard accessible with ARIA labels. Reminder management UI must support screen readers. Overdue indicators must use text labels in addition to color coding.
