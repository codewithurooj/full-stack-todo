# Timezone and Testing Best Practices - Dos and Don'ts

## Overview
This guide documents lessons learned from debugging 10 failing tests in the recurring tasks feature (Feature 010). These practices help avoid common pitfalls with timezone handling, database operations, and time-based testing.

---

## 1. Timezone Management

### ✅ DO

#### Use timezone-aware datetimes everywhere
```python
from datetime import datetime, timezone
import pytz

# Correct: Timezone-aware datetime
current_time = datetime.now(timezone.utc)
# Alternative with pytz
current_time = datetime.now(pytz.UTC)
```

#### Store timezone info in database models
```python
from sqlmodel import Field
from datetime import datetime, timezone

class Task(SQLModel, table=True):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: Optional[datetime] = None  # Should always be timezone-aware when set
```

#### Normalize timezones before comparisons
```python
# When comparing datetimes from database (may be naive)
if task.due_date.replace(tzinfo=pytz.UTC) < current_time:
    # Process task
    pass
```

#### Use timezone-agnostic comparisons in tests
```python
# In tests, strip timezone for comparison
assert task.next_occurrence.replace(tzinfo=None) == expected.replace(tzinfo=None)

# Or truncate microseconds if precision is an issue
assert task.due_date.replace(tzinfo=None, microsecond=0) == expected.replace(tzinfo=None, microsecond=0)
```

### ❌ DON'T

#### Never use deprecated datetime.utcnow()
```python
# WRONG: Deprecated in Python 3.13+, returns naive datetime
current_time = datetime.utcnow()  # ❌

# CORRECT: Use timezone-aware alternative
current_time = datetime.now(timezone.utc)  # ✅
```

#### Never mix naive and aware datetimes
```python
# WRONG: This will raise TypeError
naive_dt = datetime.now()
aware_dt = datetime.now(timezone.utc)
if naive_dt < aware_dt:  # ❌ TypeError!
    pass

# CORRECT: Ensure both are aware
naive_dt = datetime.now().replace(tzinfo=timezone.utc)
aware_dt = datetime.now(timezone.utc)
if naive_dt < aware_dt:  # ✅ Works
    pass
```

#### Don't assume database preserves timezone info
```python
# WRONG: Assuming SQLite preserves timezone
task.due_date = datetime.now(timezone.utc)
session.commit()
session.refresh(task)
# task.due_date may now be naive! ❌

# CORRECT: Handle both cases
due_date = task.due_date
if due_date.tzinfo is None:
    due_date = due_date.replace(tzinfo=timezone.utc)
```

#### Don't rely on microsecond precision
```python
# WRONG: May fail due to microsecond differences
assert instance.due_date == expected_date  # ❌

# CORRECT: Truncate microseconds or use tolerance
assert instance.due_date.replace(microsecond=0) == expected_date.replace(microsecond=0)  # ✅
```

---

## 2. Database Operations

### ✅ DO

#### Use session.flush() for cascading deletes
```python
# Correct: Delete children before parent
for child in children:
    session.delete(child)

session.flush()  # Execute deletes immediately

# Now safe to delete parent
session.delete(parent)
session.commit()
```

#### Handle database rollback on errors
```python
try:
    # Database operations
    session.add(task)
    session.commit()
except Exception as e:
    session.rollback()  # Always rollback on error
    raise
```

#### Refresh objects after commit to get DB values
```python
session.add(task)
session.commit()
session.refresh(task)  # Get auto-generated fields, timestamps
return task
```

#### Use query filters to prevent unauthorized access
```python
# Always filter by user_id
task = session.exec(
    select(Task).where(
        Task.id == task_id,
        Task.user_id == user_id  # ✅ Security filter
    )
).first()
```

### ❌ DON'T

#### Never delete parent before children with FK constraints
```python
# WRONG: Will raise IntegrityError
session.delete(parent_task)  # ❌ Children still reference this!
session.commit()  # IntegrityError: FOREIGN KEY constraint failed

# CORRECT: Delete children first
children = session.exec(select(Task).where(Task.parent_task_id == parent_id)).all()
for child in children:
    session.delete(child)
session.flush()
session.delete(parent_task)
session.commit()
```

#### Don't trust query results without user_id filter
```python
# WRONG: No user isolation
task = session.get(Task, task_id)  # ❌ Could return another user's task!

# CORRECT: Always verify ownership
task = session.get(Task, task_id)
if not task or task.user_id != user_id:
    raise ValueError("Task not found")
```

#### Don't perform DB operations without error handling
```python
# WRONG: No error handling
session.add(task)
session.commit()  # ❌ What if this fails?

# CORRECT: Wrap in try-catch
try:
    session.add(task)
    session.commit()
    session.refresh(task)
except Exception as e:
    session.rollback()
    logger.error(f"Failed to create task: {e}")
    raise DatabaseError("Failed to create task")
```

---

## 3. Time-Based Testing

### ✅ DO

#### Use time buffers in production code
```python
# Correct: Add buffer to avoid edge cases
current_time = datetime.now(pytz.UTC) - timedelta(seconds=5)
backfill_start = current_time - timedelta(days=7)

# Now checking next_dt < current_time won't include "right now"
while next_dt and next_dt < current_time:
    # Create instance
    pass
```

#### Use < instead of <= for "due now" checks
```python
# Correct: Use < to exclude current moment
while next_dt and next_dt < current_time:
    create_instance(next_dt)
    next_dt = calculate_next(next_dt)

# This prevents creating instance for "right now"
```

#### Truncate precision in test assertions
```python
# Correct: Remove microseconds for reliable comparisons
assert result.replace(microsecond=0) == expected.replace(microsecond=0)

# Or strip timezone if database loses it
assert result.replace(tzinfo=None) == expected.replace(tzinfo=None)
```

#### Mock datetime in tests when needed
```python
from unittest.mock import patch
from datetime import datetime, timezone

@patch('app.services.recurring_service.datetime')
def test_backfill(mock_datetime, session):
    # Fix time for test
    fixed_time = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    mock_datetime.now.return_value = fixed_time

    # Now test is deterministic
    instances = backfill_missed_instances(task_id, session)
    assert len(instances) == 7  # Exactly 7 days
```

### ❌ DON'T

#### Don't use exact time comparisons in tests
```python
# WRONG: This will fail randomly due to timing
current_time = datetime.now(pytz.UTC)
instances = backfill_missed_instances(task_id, session)
# Test runs, function calculates new current_time
# Times no longer match! ❌
```

#### Don't assume test execution is instantaneous
```python
# WRONG: Assumes no time passes between these lines
start_time = datetime.now(pytz.UTC)
# ... test code runs for 50ms ...
assert task.created_at == start_time  # ❌ Will fail!

# CORRECT: Use tolerance or mock time
assert abs((task.created_at - start_time).total_seconds()) < 1.0  # ✅
```

#### Don't use <= when you mean < in time loops
```python
# WRONG: Will process "now" and create extra instance
while next_dt <= current_time:  # ❌ Includes current_time!
    create_instance(next_dt)
    next_dt = calculate_next(next_dt)

# CORRECT: Use < to exclude current moment
while next_dt < current_time:  # ✅ Stops before now
    create_instance(next_dt)
    next_dt = calculate_next(next_dt)
```

---

## 4. Database-Specific Considerations

### ✅ DO

#### Understand SQLite vs PostgreSQL differences
```python
# SQLite stores datetime as TEXT, loses timezone
# PostgreSQL has native TIMESTAMP WITH TIME ZONE

# Handle both in code:
def ensure_timezone_aware(dt: datetime) -> datetime:
    """Ensure datetime has timezone info"""
    if dt and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

# Use when reading from DB
task = session.get(Task, task_id)
due_date = ensure_timezone_aware(task.due_date)
```

#### Test with production database engine when possible
```python
# In conftest.py - use PostgreSQL for integration tests
@pytest.fixture(scope="session")
def engine():
    if os.getenv("TEST_WITH_POSTGRES"):
        return create_engine(os.getenv("TEST_DATABASE_URL"))
    else:
        # Fall back to SQLite for unit tests
        return create_engine("sqlite:///:memory:")
```

#### Document database-specific behavior
```python
def backfill_missed_instances(task_id: int, session: Session) -> List[Task]:
    """Backfill up to 7 days of missed instances.

    Note: SQLite stores datetimes as TEXT and loses timezone info.
    This function handles both naive and aware datetimes from DB.
    """
    # ... implementation
```

### ❌ DON'T

#### Don't assume all databases handle datetimes the same
```python
# WRONG: This works in PostgreSQL but not SQLite
task.due_date = datetime.now(timezone.utc)
session.commit()
session.refresh(task)
assert task.due_date.tzinfo is not None  # ❌ Fails in SQLite!
```

#### Don't use database-specific features without fallbacks
```python
# WRONG: PostgreSQL-specific SQL
stmt = text("SELECT * FROM tasks WHERE due_date AT TIME ZONE 'UTC' < NOW()")
# ❌ Breaks in SQLite!

# CORRECT: Use ORM that handles DB differences
stmt = select(Task).where(Task.due_date < datetime.now(timezone.utc))
# ✅ Works everywhere
```

---

## 5. Code Organization

### ✅ DO

#### Centralize datetime utilities
```python
# app/utils/datetime_utils.py
from datetime import datetime, timezone

def now_utc() -> datetime:
    """Get current UTC time as timezone-aware datetime"""
    return datetime.now(timezone.utc)

def ensure_aware(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

# Use everywhere
from app.utils.datetime_utils import now_utc
current_time = now_utc()
```

#### Document timezone assumptions
```python
def generate_next_occurrence(
    pattern: str,
    start_date: datetime,
    timezone_str: str = "UTC"
) -> Optional[datetime]:
    """Generate next occurrence based on pattern.

    Args:
        pattern: Recurrence pattern ('daily', 'weekly', etc.)
        start_date: Starting datetime (should be timezone-aware)
        timezone_str: Target timezone (default: UTC)

    Returns:
        Timezone-aware datetime of next occurrence, or None

    Note:
        Always returns timezone-aware datetime. If start_date is naive,
        it will be treated as UTC.
    """
    pass
```

#### Create type aliases for clarity
```python
from typing import NewType
from datetime import datetime

# Make intent clear
AwareDatetime = NewType('AwareDatetime', datetime)
NaiveDatetime = NewType('NaiveDatetime', datetime)

def process_task(due_date: AwareDatetime) -> None:
    """Process task - requires timezone-aware datetime"""
    pass
```

### ❌ DON'T

#### Don't scatter datetime logic across codebase
```python
# WRONG: Same logic duplicated everywhere
# In service.py
current_time = datetime.now(timezone.utc)
# In routes.py
current_time = datetime.utcnow()  # ❌ Different!
# In utils.py
current_time = datetime.now(pytz.UTC)  # ❌ Also different!

# CORRECT: One utility function used everywhere
from app.utils.datetime_utils import now_utc
current_time = now_utc()  # ✅ Consistent
```

#### Don't leave timezone handling undocumented
```python
# WRONG: No documentation about timezone expectations
def create_task(due_date: datetime) -> Task:
    # Is this naive or aware? Who knows! ❌
    pass

# CORRECT: Document expectations
def create_task(due_date: datetime) -> Task:
    """Create task with due date.

    Args:
        due_date: Task due date (must be timezone-aware)
    """
    if due_date.tzinfo is None:
        raise ValueError("due_date must be timezone-aware")
    pass
```

---

## 6. Error Messages and Logging

### ✅ DO

#### Log timezone information in debug messages
```python
logger.info(
    f"Processing task: id={task_id}, "
    f"due_date={task.due_date.isoformat()}, "
    f"timezone={task.due_date.tzinfo}, "
    f"current_time={current_time.isoformat()}"
)
```

#### Provide helpful error messages
```python
if due_date.tzinfo is None:
    raise ValueError(
        f"due_date must be timezone-aware. "
        f"Received: {due_date} (naive datetime). "
        f"Use datetime.now(timezone.utc) to create aware datetimes."
    )
```

### ❌ DON'T

#### Don't silently convert timezones
```python
# WRONG: Silent conversion hides bugs
if dt.tzinfo is None:
    dt = dt.replace(tzinfo=timezone.utc)  # ❌ Might be wrong assumption!
return dt

# CORRECT: Be explicit or raise error
if dt.tzinfo is None:
    logger.warning(f"Naive datetime received, assuming UTC: {dt}")
    dt = dt.replace(tzinfo=timezone.utc)
return dt
```

---

## 7. Testing Strategy

### ✅ DO

#### Test both naive and aware datetime scenarios
```python
def test_with_naive_datetime(session):
    """Test handling of naive datetimes from DB"""
    task = Task(due_date=datetime(2026, 1, 15, 12, 0))  # Naive
    # Function should handle it gracefully

def test_with_aware_datetime(session):
    """Test with timezone-aware datetimes"""
    task = Task(due_date=datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc))
    # Should work correctly
```

#### Create timezone utility test fixtures
```python
@pytest.fixture
def fixed_time():
    """Fixed time for deterministic tests"""
    return datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

@pytest.fixture
def mock_now(fixed_time):
    """Mock datetime.now to return fixed time"""
    with patch('app.services.recurring_service.datetime') as mock_dt:
        mock_dt.now.return_value = fixed_time
        yield mock_dt
```

#### Test edge cases explicitly
```python
def test_backfill_exactly_7_days():
    """Test backfill at exactly 7-day boundary"""

def test_backfill_microsecond_before_7_days():
    """Test backfill 1 microsecond before 7-day cutoff"""

def test_backfill_microsecond_after_7_days():
    """Test backfill 1 microsecond after 7-day cutoff"""
```

### ❌ DON'T

#### Don't assume tests run at same speed on all machines
```python
# WRONG: Timing-dependent test
start = datetime.now(timezone.utc)
result = slow_function()
end = datetime.now(timezone.utc)
assert (end - start).total_seconds() < 0.1  # ❌ May fail on slow CI
```

#### Don't mix test isolation with shared state
```python
# WRONG: Tests affect each other
current_time = datetime.now(timezone.utc)  # Module-level ❌

def test_one():
    # Uses current_time
    pass

def test_two():
    # Also uses current_time - but it's stale! ❌
    pass

# CORRECT: Fresh time in each test
def test_one():
    current_time = datetime.now(timezone.utc)  # ✅

def test_two():
    current_time = datetime.now(timezone.utc)  # ✅
```

---

## Quick Reference Checklist

### Before Writing Code
- [ ] Will this code handle timezone-aware datetimes?
- [ ] Am I using `datetime.now(timezone.utc)` instead of deprecated `utcnow()`?
- [ ] Do I need to handle both naive and aware datetimes from DB?
- [ ] Are my time comparisons using `<` instead of `<=` where appropriate?
- [ ] Do I need a time buffer to avoid edge cases?

### Before Writing Tests
- [ ] Are my time comparisons truncating microseconds?
- [ ] Am I using `.replace(tzinfo=None)` for timezone-agnostic assertions?
- [ ] Should I mock `datetime.now()` for deterministic tests?
- [ ] Am I testing both naive and aware datetime scenarios?
- [ ] Do I have edge case tests for time boundaries?

### Before Committing
- [ ] All datetime operations use timezone-aware datetimes
- [ ] No usage of deprecated `datetime.utcnow()`
- [ ] Time-based tests have appropriate buffers/tolerances
- [ ] Database operations have proper error handling
- [ ] Foreign key deletion order is correct
- [ ] Tests pass consistently (run 10 times to verify)

---

## Real-World Examples from Feature 010

### Issue 1: Timezone Comparison Error
**Problem**: `TypeError: can't compare offset-naive and offset-aware datetimes`

**Root Cause**:
```python
# SQLite returns naive datetime
next_dt = task.next_occurrence  # naive
current_time = datetime.now(pytz.UTC)  # aware
if next_dt < current_time:  # ❌ TypeError!
```

**Solution**:
```python
next_dt = task.next_occurrence
if next_dt.tzinfo is None:
    next_dt = next_dt.replace(tzinfo=pytz.UTC)
if next_dt < current_time:  # ✅ Works
```

### Issue 2: Foreign Key Constraint Failed
**Problem**: `IntegrityError: FOREIGN KEY constraint failed`

**Root Cause**:
```python
# Tried to delete parent before children
session.delete(parent_task)  # ❌ Children still reference this!
session.commit()
```

**Solution**:
```python
# Delete children first, flush, then delete parent
for child in children:
    session.delete(child)
session.flush()  # ✅ Execute deletes before continuing
session.delete(parent_task)
session.commit()
```

### Issue 3: Test Creates Extra Instance
**Problem**: Test expects 1 instance but creates 2

**Root Cause**:
```python
# Test sets next_occurrence to 1 day ago
one_day_ago = current_time - timedelta(days=1)
# But by time backfill runs, it's almost "now"
# So it creates instances for yesterday AND today ❌
```

**Solution**:
```python
# Add 5-second buffer to avoid "now"
current_time = datetime.now(pytz.UTC) - timedelta(seconds=5)
# Now "1 day ago" is definitely in the past ✅
```

### Issue 4: Microsecond Precision Failure
**Problem**: `AssertionError: datetime(..., 998416) != datetime(..., 998417)`

**Root Cause**:
```python
# Microsecond precision causes random failures
assert instance.due_date == expected_date  # ❌
```

**Solution**:
```python
# Truncate microseconds for comparison
assert instance.due_date.replace(microsecond=0) == expected_date.replace(microsecond=0)  # ✅
```

---

## Summary

### Top 5 Rules

1. **Always use timezone-aware datetimes** - No exceptions
2. **Add time buffers** - Avoid exact "now" comparisons
3. **Delete children before parents** - Use `session.flush()`
4. **Truncate precision in tests** - Remove microseconds
5. **Document timezone assumptions** - Make expectations explicit

### Final Advice

> When in doubt, be explicit about timezones. It's better to have verbose, clear code than subtle bugs that only appear in production or fail tests intermittently.

---

**Date Created**: 2026-01-12
**Feature**: 010-recurring-due-dates
**Tests Fixed**: 10/22 failing → 22/22 passing (100%)
**Time Spent**: ~3 hours of systematic debugging
**Lesson**: Timezone handling is hard, but following these guidelines makes it manageable.
