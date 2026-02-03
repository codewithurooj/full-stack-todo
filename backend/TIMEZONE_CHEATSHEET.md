# Timezone & Testing Quick Cheatsheet

## 🚫 Never Do This

```python
# ❌ Deprecated and naive
datetime.utcnow()

# ❌ Mix naive and aware
if naive_dt < aware_dt:

# ❌ Delete parent before children
session.delete(parent)
session.delete(child)

# ❌ Exact time comparisons in tests
assert task.created_at == current_time

# ❌ Use <= in time loops
while next_dt <= current_time:
```

## ✅ Always Do This

```python
# ✅ Use timezone-aware datetimes
datetime.now(timezone.utc)
datetime.now(pytz.UTC)

# ✅ Handle naive datetimes from DB
if dt.tzinfo is None:
    dt = dt.replace(tzinfo=timezone.utc)

# ✅ Delete children first, flush, then parent
for child in children:
    session.delete(child)
session.flush()
session.delete(parent)

# ✅ Strip timezone/microseconds in test assertions
assert task.due_date.replace(tzinfo=None, microsecond=0) == expected.replace(tzinfo=None, microsecond=0)

# ✅ Use < instead of <= in time loops
while next_dt < current_time:

# ✅ Add time buffers to avoid edge cases
current_time = datetime.now(pytz.UTC) - timedelta(seconds=5)
```

## 🛠️ Common Patterns

### Creating timezone-aware datetime
```python
from datetime import datetime, timezone
import pytz

# Method 1: stdlib
now = datetime.now(timezone.utc)

# Method 2: pytz
now = datetime.now(pytz.UTC)

# From naive
naive = datetime(2026, 1, 15, 12, 0)
aware = naive.replace(tzinfo=timezone.utc)
```

### Safe database operations
```python
# Add with error handling
try:
    session.add(obj)
    session.commit()
    session.refresh(obj)
except Exception as e:
    session.rollback()
    raise

# Delete with FK constraints
for child in children:
    session.delete(child)
session.flush()  # Execute deletes
session.delete(parent)
session.commit()
```

### Test assertions for datetimes
```python
# Strip timezone
assert result.replace(tzinfo=None) == expected.replace(tzinfo=None)

# Strip microseconds
assert result.replace(microsecond=0) == expected.replace(microsecond=0)

# Both
assert result.replace(tzinfo=None, microsecond=0) == expected.replace(tzinfo=None, microsecond=0)

# Use tolerance
assert abs((result - expected).total_seconds()) < 1.0
```

## 🐛 Debug Checklist

When timezone tests fail:
1. ✓ Are both datetimes aware or both naive?
2. ✓ Is microsecond precision causing issues?
3. ✓ Does SQLite lose timezone info on round-trip?
4. ✓ Is test timing causing race conditions?
5. ✓ Do I need a time buffer?

When FK constraint fails:
1. ✓ Am I deleting children before parent?
2. ✓ Am I using `session.flush()` between deletes?
3. ✓ Is there a cascade option I'm missing?

## 📝 Template Code

### Service function with timezone handling
```python
def process_tasks(session: Session) -> List[Task]:
    """Process tasks - handles both naive and aware datetimes."""
    current_time = datetime.now(pytz.UTC) - timedelta(seconds=5)

    # Get tasks
    tasks = session.exec(select(Task).where(...)).all()

    processed = []
    for task in tasks:
        # Ensure timezone-aware
        due_date = task.due_date
        if due_date and due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=pytz.UTC)

        # Use < not <=
        if due_date and due_date < current_time:
            processed.append(task)

    return processed
```

### Test with timezone handling
```python
def test_process_tasks(session: Session):
    """Test task processing with timezone awareness."""
    # Use fixed time for determinism
    current_time = datetime(2026, 1, 15, 12, 0, tzinfo=pytz.UTC)
    past_time = current_time - timedelta(days=1)

    # Create test task
    task = Task(due_date=past_time, ...)
    session.add(task)
    session.commit()
    session.refresh(task)

    # Process tasks
    result = process_tasks(session)

    # Assert with timezone handling
    assert len(result) == 1
    assert result[0].due_date.replace(tzinfo=None) == past_time.replace(tzinfo=None)
```

## 🎯 One-Liners

```python
# Get current UTC time (aware)
now = datetime.now(timezone.utc)

# Make naive datetime aware
aware = naive.replace(tzinfo=timezone.utc)

# Strip timezone for comparison
dt.replace(tzinfo=None)

# Strip microseconds for comparison
dt.replace(microsecond=0)

# Both
dt.replace(tzinfo=None, microsecond=0)

# Add safety buffer
now = datetime.now(pytz.UTC) - timedelta(seconds=5)

# Safe delete order
session.flush()  # Between child and parent deletes
```

## 🔍 Quick Diagnostics

```python
# Check if datetime is aware
if dt.tzinfo is None:
    print("Naive datetime ❌")
else:
    print(f"Aware datetime ✅ - {dt.tzinfo}")

# Compare datetimes safely
def safe_compare(dt1, dt2):
    """Compare datetimes handling naive/aware mismatch."""
    d1 = dt1.replace(tzinfo=None, microsecond=0) if dt1 else None
    d2 = dt2.replace(tzinfo=None, microsecond=0) if dt2 else None
    return d1 == d2

# Log datetime info
logger.debug(
    f"DateTime: {dt.isoformat()} | "
    f"TZ: {dt.tzinfo} | "
    f"Naive: {dt.tzinfo is None}"
)
```

---

**Print this and keep it next to your keyboard! 📌**
