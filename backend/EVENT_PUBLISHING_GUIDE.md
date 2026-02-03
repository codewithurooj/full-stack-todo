# Event Publishing Implementation Guide

**Feature 011: Kafka Event-Driven Architecture**
**Task:** Add event publishing to task CRUD operations
**File:** `backend/app/routes/tasks.py`

## Overview

This guide shows exactly where to add Kafka event publishing calls in the task routes. The event publisher module (`app/services/event_publisher.py`) has already been created and registered in `main.py`.

## Step 1: Add Import

**Location:** Top of `backend/app/routes/tasks.py` (after line 13)

**Add this line:**
```python
# Kafka event publishing (Feature 011)
from app.services.event_publisher import publish_task_event
```

**Full imports section should look like:**
```python
from app.utils.query_builder import build_tasks_query
from app.utils.validation import validate_priority, validate_tags, validate_date_range
from pydantic import BaseModel

# Kafka event publishing (Feature 011)
from app.services.event_publisher import publish_task_event

# Setup logger
logger = logging.getLogger(__name__)
```

## Step 2: Add Event Publishing to create_task

**Location:** After line 209 (after logger.info, before return)

**Add these lines:**
```python
    logger.info(
        f"create_task: user={user_id}, task_id={db_task.id}, "
        f"priority={db_task.priority}, tags_count={len(db_task.tags)}"
    )

    # Publish task.created event (Feature 011)
    await publish_task_event(
        event_type="task.created",
        user_id=user_id,
        task_id=db_task.id,
        task_data=db_task.model_dump()
    )

    return db_task
```

## Step 3: Add Event Publishing to update_task

**Location:** After line 325 (after logger.info, before return)

**Find this code:**
```python
    logger.info(
        f"update_task: user={user_id}, task_id={task_id}, "
        f"updated_fields={list(update_data.keys())}"
    )

    return db_task
```

**Change to:**
```python
    logger.info(
        f"update_task: user={user_id}, task_id={task_id}, "
        f"updated_fields={list(update_data.keys())}"
    )

    # Publish task.updated event (Feature 011)
    await publish_task_event(
        event_type="task.updated",
        user_id=user_id,
        task_id=db_task.id,
        task_data=db_task.model_dump()
    )

    return db_task
```

## Step 4: Add Event Publishing to delete_task

**Location:** After line 368 (after session.commit())

**Find this code:**
```python
    # Delete task
    session.delete(task)
    session.commit()
```

**Change to:**
```python
    # Delete task
    session.delete(task)
    session.commit()

    # Publish task.deleted event (Feature 011)
    await publish_task_event(
        event_type="task.deleted",
        user_id=user_id,
        task_id=task_id,
        task_data={"deleted": True, "title": task.title}
    )
```

## Step 5: Add Event Publishing to toggle_complete

**Location:** After line 417 (inside the completion block)

**Find this code:**
```python
    session.add(db_task)
    session.commit()
    session.refresh(db_task)

    # If task is now completed and has recurring pattern, generate next instance
    if db_task.completed and db_task.recurring_pattern and db_task.recurring_pattern != 'none':
```

**Change to:**
```python
    session.add(db_task)
    session.commit()
    session.refresh(db_task)

    # Publish task.completed event if task was marked as complete (Feature 011)
    if db_task.completed:
        await publish_task_event(
            event_type="task.completed",
            user_id=user_id,
            task_id=db_task.id,
            task_data=db_task.model_dump()
        )

    # If task is now completed and has recurring pattern, generate next instance
    if db_task.completed and db_task.recurring_pattern and db_task.recurring_pattern != 'none':
```

## Verification

After making these changes, restart the FastAPI server and check:

1. **Startup logs should show:**
   ```
   Kafka producer started successfully
   ```

2. **Health check should show Kafka status:**
   ```bash
   curl http://localhost:8000/health
   ```
   Should return:
   ```json
   {
     "status": "healthy",
     "kafka_producer": {
       "status": "healthy",
       "metrics": {
         "publish_count": 0,
         "error_count": 0,
         "avg_latency_ms": 0
       }
     }
   }
   ```

3. **Create a task and check logs:**
   ```bash
   # Create task
   curl -X POST http://localhost:8000/api/user123/tasks \
     -H "Authorization: Bearer YOUR_JWT" \
     -H "Content-Type: application/json" \
     -d '{"title": "Test task", "description": "Testing events"}'

   # Check server logs for:
   # - "create_task: user=user123, task_id=X, ..."
   # - Kafka publish confirmation
   ```

4. **Check Kafka topic (if Redpanda running):**
   ```bash
   docker exec -it redpanda rpk topic consume task-events --num 1
   ```

## Event Schema

All events follow this schema (defined in `backend/app/schemas/events.py`):

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "task.created",
  "schema_version": "1.0.0",
  "timestamp": "2026-01-13T12:00:00Z",
  "user_id": "user123",
  "task_id": 42,
  "task_data": {
    "id": 42,
    "title": "Buy groceries",
    "description": "Milk, bread, eggs",
    "completed": false,
    "priority": "high",
    "tags": ["shopping"],
    "created_at": "2026-01-13T12:00:00Z",
    "updated_at": "2026-01-13T12:00:00Z"
  }
}
```

## Error Handling

The event publisher is designed to **never block task operations**:

- If Kafka is unavailable, events are logged but not published
- If publish fails, error is logged but operation succeeds
- Application continues without Kafka (graceful degradation)

## Next Steps

After adding event publishing:

1. ✅ Start Redpanda: `docker-compose -f docker-compose-kafka.yml up -d`
2. ✅ Restart backend: `uvicorn app.main:app --reload`
3. ✅ Test task operations (create, update, delete, complete)
4. ✅ Verify events are published to Kafka
5. ✅ Build Recurring Task Service microservice to consume events
6. ✅ Build Audit Service microservice to consume events

---

**Implementation Status:**
☐ Import added
☐ create_task event added
☐ update_task event added
☐ delete_task event added
☐ toggle_complete event added

**Once complete, mark tasks in:** `specs/011-kafka-event-architecture/tasks.md`
- [X] T035: Publish task.completed event in complete_task endpoint
- [X] T036: Include full task_data in event payload
- [X] T037: Add event publishing error handling
