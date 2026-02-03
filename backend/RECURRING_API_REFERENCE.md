# Recurring Tasks API Reference

## Overview
This document provides a quick reference for the recurring tasks API endpoints implemented in Feature 010.

## Base URL
```
http://localhost:8000/api/{user_id}/tasks
```

## Endpoints

### 1. Set Recurring Pattern

**Endpoint**: `PUT /api/{user_id}/tasks/{task_id}/recurring`

**Description**: Create or update a recurring pattern on an existing task.

**Requirements**:
- Task must have a `due_date` set
- User must be authenticated (JWT)
- `user_id` in path must match JWT token

**Request Body**:
```json
{
  "pattern": "daily" | "weekly" | "monthly" | "custom",
  "interval": 1,
  "days": ["Mon", "Wed", "Fri"],  // Optional, for weekly patterns
  "end_date": "2026-12-31T23:59:59Z"  // Optional
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "title": "Daily standup",
  "user_id": "user123",
  "due_date": "2026-01-15T09:00:00Z",
  "recurring_pattern": "daily",
  "recurring_interval": 1,
  "recurring_days": null,
  "recurring_end_date": "2026-12-31T23:59:59Z",
  "next_occurrence": "2026-01-16T09:00:00Z",
  "parent_task_id": null,
  "completed": false,
  "created_at": "2026-01-15T08:00:00Z",
  "updated_at": "2026-01-15T08:30:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid pattern, task has no due_date, or validation error
- `403 Forbidden`: Unauthorized (user_id mismatch)
- `404 Not Found`: Task not found
- `500 Internal Server Error`: Failed to set pattern

**Example**:
```bash
curl -X PUT http://localhost:8000/api/user123/tasks/1/recurring \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "weekly",
    "interval": 1,
    "days": ["Mon", "Wed", "Fri"],
    "end_date": "2026-06-30T23:59:59Z"
  }'
```

---

### 2. Remove Recurring Pattern

**Endpoint**: `DELETE /api/{user_id}/tasks/{task_id}/recurring`

**Description**: Remove recurring pattern from a task with deletion options.

**Query Parameters**:
- `delete_type` (optional): Deletion strategy
  - `this_only` (default): Remove pattern from this task only
  - `this_and_future`: Remove pattern + delete future instances
  - `all`: Delete parent task + all instances

**Response**: `204 No Content`

**Error Responses**:
- `403 Forbidden`: Unauthorized
- `404 Not Found`: Task not found
- `500 Internal Server Error`: Failed to remove pattern

**Examples**:

**Option 1: Remove pattern only (keep instances)**
```bash
curl -X DELETE "http://localhost:8000/api/user123/tasks/1/recurring?delete_type=this_only" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Option 2: Remove pattern and delete future instances**
```bash
curl -X DELETE "http://localhost:8000/api/user123/tasks/1/recurring?delete_type=this_and_future" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Option 3: Delete everything (parent + all instances)**
```bash
curl -X DELETE "http://localhost:8000/api/user123/tasks/1/recurring?delete_type=all" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

### 3. Calculate Next Occurrence

**Endpoint**: `POST /api/{user_id}/tasks/{task_id}/next-occurrence`

**Description**: Calculate the next occurrence for a recurring task without creating an instance.

**Requirements**:
- Task must have `recurring_pattern` set
- Task must have `due_date` set

**Response** (200 OK):
```json
{
  "next_occurrence": "2026-01-16T09:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Task is not recurring or has no due_date
- `403 Forbidden`: Unauthorized
- `404 Not Found`: Task not found
- `500 Internal Server Error`: Failed to calculate

**Example**:
```bash
curl -X POST http://localhost:8000/api/user123/tasks/1/next-occurrence \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## Recurring Pattern Formats

### Daily
```json
{
  "pattern": "daily",
  "interval": 1  // Every day
}
```

```json
{
  "pattern": "daily",
  "interval": 2  // Every 2 days
}
```

### Weekly
```json
{
  "pattern": "weekly",
  "interval": 1,
  "days": ["Mon", "Wed", "Fri"]  // Every Monday, Wednesday, Friday
}
```

```json
{
  "pattern": "weekly",
  "interval": 2,
  "days": ["Mon"]  // Every other Monday
}
```

**Valid day abbreviations**: `Mon`, `Tue`, `Wed`, `Thu`, `Fri`, `Sat`, `Sun`

### Monthly
```json
{
  "pattern": "monthly",
  "interval": 1  // Every month on same day
}
```

```json
{
  "pattern": "monthly",
  "interval": 3  // Every 3 months (quarterly)
}
```

### With End Date
```json
{
  "pattern": "daily",
  "interval": 1,
  "end_date": "2026-12-31T23:59:59Z"  // Stops after this date
}
```

---

## Automatic Instance Generation

### Background Job
The recurring task generator runs automatically every 1 minute:
- Queries tasks where `next_occurrence <= current_time`
- Generates new instance for each task
- Updates parent's `next_occurrence`
- Logs success/failure

### Manual Trigger (Completion Hook)
When a recurring task is marked complete:
- Next instance is generated immediately
- Parent's `next_occurrence` is updated
- If generation fails, completion still succeeds

---

## Task Instance Fields

### Parent Task (Recurring Template)
```json
{
  "id": 1,
  "title": "Daily standup",
  "recurring_pattern": "daily",
  "recurring_interval": 1,
  "next_occurrence": "2026-01-16T09:00:00Z",
  "parent_task_id": null  // Parent tasks have null
}
```

### Child Instance (Generated)
```json
{
  "id": 2,
  "title": "Daily standup",
  "recurring_pattern": null,  // Instances are NOT recurring
  "recurring_interval": null,
  "next_occurrence": null,
  "parent_task_id": 1,  // Points to parent
  "due_date": "2026-01-16T09:00:00Z",
  "completed": false
}
```

---

## Common Workflows

### 1. Create Daily Recurring Task
```bash
# Step 1: Create task with due_date
curl -X POST http://localhost:8000/api/user123/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Daily standup",
    "due_date": "2026-01-15T09:00:00Z"
  }'

# Step 2: Set recurring pattern
curl -X PUT http://localhost:8000/api/user123/tasks/1/recurring \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "daily",
    "interval": 1
  }'
```

### 2. Create Weekly Recurring Task (Mon/Wed/Fri)
```bash
# Create task
curl -X POST http://localhost:8000/api/user123/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Team meeting",
    "due_date": "2026-01-13T10:00:00Z"
  }'

# Set weekly pattern
curl -X PUT http://localhost:8000/api/user123/tasks/2/recurring \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "weekly",
    "interval": 1,
    "days": ["Mon", "Wed", "Fri"]
  }'
```

### 3. Stop Recurring Pattern (Keep Instances)
```bash
curl -X DELETE "http://localhost:8000/api/user123/tasks/1/recurring?delete_type=this_only" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Delete Recurring Series (Parent + All Instances)
```bash
curl -X DELETE "http://localhost:8000/api/user123/tasks/1/recurring?delete_type=all" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Edge Cases

### Backfill Behavior
If a task's `next_occurrence` is in the past:
- Automatic backfill generates up to 7 days of missed instances
- Older instances beyond 7 days are NOT generated
- Prevents overwhelming users who return after long absence

### End Date Behavior
When `recurring_end_date` is reached:
- No more instances are generated
- `next_occurrence` becomes `null`
- Parent task remains in database

### Timezone Handling
- All dates stored in UTC (TIMESTAMPTZ)
- Pattern generation uses UTC timezone
- Frontend should convert to user's local timezone for display

---

## Service Functions (For Internal Use)

Located in `app/services/recurring_service.py`:

```python
# Set recurring pattern
task = set_recurring_pattern(
    task_id=1,
    pattern="daily",
    interval=1,
    days=None,
    end_date=None,
    user_id="user123",
    session=session
)

# Generate next instance
instance = generate_recurring_instances(task_id=1, session=session)

# Backfill missed instances
instances = backfill_missed_instances(task_id=1, session=session)

# Get tasks due for generation
tasks = get_recurring_tasks_due(session=session)

# Get all instances
instances = get_task_instances(parent_task_id=1, session=session)
```

---

## Testing Examples

### Test Daily Pattern
```python
def test_daily_recurring():
    # Create task
    task = Task(
        user_id="test_user",
        title="Daily task",
        due_date=datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)
    )
    session.add(task)
    session.commit()

    # Set pattern
    updated = set_recurring_pattern(
        task_id=task.id,
        pattern="daily",
        interval=1,
        days=None,
        end_date=None,
        user_id="test_user",
        session=session
    )

    assert updated.recurring_pattern == "daily"
    assert updated.next_occurrence == datetime(2026, 1, 16, 9, 0, tzinfo=pytz.UTC)
```

---

## Troubleshooting

### Issue: Cannot Set Recurring Pattern
**Error**: `400 Bad Request: Task must have a due_date`

**Solution**: Ensure task has `due_date` set before setting recurring pattern:
```bash
# First update task with due_date
curl -X PUT http://localhost:8000/api/user123/tasks/1 \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"due_date": "2026-01-15T09:00:00Z"}'

# Then set recurring pattern
curl -X PUT http://localhost:8000/api/user123/tasks/1/recurring \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"pattern": "daily", "interval": 1}'
```

### Issue: Instances Not Generating
**Check**:
1. Is scheduler running? (Check logs: "Added job: recurring_generator")
2. Is `next_occurrence` set and in the past?
3. Is `recurring_pattern` not null?

---

**For full implementation details, see**: `RECURRING_IMPLEMENTATION_SUMMARY.md`
