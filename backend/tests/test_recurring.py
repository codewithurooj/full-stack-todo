"""Tests for recurring task functionality"""
import pytest
from datetime import datetime, timedelta
from sqlmodel import Session, select
import pytz

from app.models.task import Task
from app.services.recurring_service import (
    set_recurring_pattern,
    remove_recurring_pattern,
    generate_recurring_instances,
    backfill_missed_instances,
    get_recurring_tasks_due,
    get_task_instances
)
from app.utils.rrule import generate_next_occurrence


# ============================================================================
# T087: Pattern creation tests
# ============================================================================

def test_create_daily_recurring_pattern(session: Session):
    """Test creating a daily recurring pattern"""
    # Create task with due_date
    due_date = datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)
    task = Task(
        user_id="test_user",
        title="Daily standup",
        due_date=due_date
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Set recurring pattern
    updated_task = set_recurring_pattern(
        task_id=task.id,
        pattern="daily",
        interval=1,
        days=None,
        end_date=None,
        user_id="test_user",
        session=session
    )

    # Verify pattern was set
    assert updated_task.recurring_pattern == "daily"
    assert updated_task.recurring_interval == 1
    assert updated_task.next_occurrence is not None

    # Verify next_occurrence is due_date + 1 day
    expected_next = due_date + timedelta(days=1)
    assert updated_task.next_occurrence.replace(tzinfo=None) == expected_next.replace(tzinfo=None)


def test_create_weekly_recurring_pattern(session: Session):
    """Test creating a weekly recurring pattern with specific days"""
    # Create task with due_date (Monday)
    due_date = datetime(2026, 1, 12, 9, 0, tzinfo=pytz.UTC)  # Monday
    task = Task(
        user_id="test_user",
        title="Team meeting",
        due_date=due_date
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Set weekly pattern on Mon, Wed, Fri
    updated_task = set_recurring_pattern(
        task_id=task.id,
        pattern="weekly",
        interval=1,
        days=["Mon", "Wed", "Fri"],
        end_date=None,
        user_id="test_user",
        session=session
    )

    # Verify pattern was set
    assert updated_task.recurring_pattern == "weekly"
    assert updated_task.recurring_interval == 1
    assert updated_task.recurring_days == ["Mon", "Wed", "Fri"]
    assert updated_task.next_occurrence is not None

    # Next occurrence should be Wednesday (2 days after Monday)
    expected_next = due_date + timedelta(days=2)
    assert updated_task.next_occurrence.replace(tzinfo=None) == expected_next.replace(tzinfo=None)


def test_create_monthly_recurring_pattern(session: Session):
    """Test creating a monthly recurring pattern"""
    # Create task with due_date (15th of month)
    due_date = datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)
    task = Task(
        user_id="test_user",
        title="Monthly report",
        due_date=due_date
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Set monthly pattern
    updated_task = set_recurring_pattern(
        task_id=task.id,
        pattern="monthly",
        interval=1,
        days=None,
        end_date=None,
        user_id="test_user",
        session=session
    )

    # Verify pattern was set
    assert updated_task.recurring_pattern == "monthly"
    assert updated_task.recurring_interval == 1
    assert updated_task.next_occurrence is not None

    # Next occurrence should be 15th of next month
    expected_next = datetime(2026, 2, 15, 9, 0, tzinfo=pytz.UTC)
    assert updated_task.next_occurrence.replace(tzinfo=None) == expected_next.replace(tzinfo=None)


def test_create_recurring_pattern_without_due_date(session: Session):
    """Test that setting recurring pattern fails without due_date"""
    # Create task without due_date
    task = Task(
        user_id="test_user",
        title="Task without due date"
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Attempt to set recurring pattern should fail
    with pytest.raises(ValueError, match="must have a due_date"):
        set_recurring_pattern(
            task_id=task.id,
            pattern="daily",
            interval=1,
            days=None,
            end_date=None,
            user_id="test_user",
            session=session
        )


def test_create_recurring_pattern_invalid_pattern(session: Session):
    """Test that invalid pattern is rejected"""
    # Create task with due_date
    due_date = datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)
    task = Task(
        user_id="test_user",
        title="Test task",
        due_date=due_date
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Attempt to set invalid pattern
    with pytest.raises(ValueError, match="Invalid pattern"):
        set_recurring_pattern(
            task_id=task.id,
            pattern="invalid_pattern",
            interval=1,
            days=None,
            end_date=None,
            user_id="test_user",
            session=session
        )


# ============================================================================
# T088: Instance generation tests
# ============================================================================

def test_generate_daily_instance(session: Session):
    """Test generating a daily recurring instance"""
    # Create recurring task (daily)
    due_date = datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)
    task = Task(
        user_id="test_user",
        title="Daily standup",
        due_date=due_date,
        recurring_pattern="daily",
        recurring_interval=1,
        next_occurrence=due_date + timedelta(days=1)
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Generate instance
    instance = generate_recurring_instances(task.id, session)

    # Verify instance was created
    assert instance is not None
    assert instance.title == task.title
    assert instance.user_id == task.user_id
    assert instance.parent_task_id == task.id
    assert instance.completed is False
    assert instance.recurring_pattern is None  # Instances are not themselves recurring

    # Verify due_date is the next day
    expected_due = due_date + timedelta(days=1)
    assert instance.due_date.replace(tzinfo=None) == expected_due.replace(tzinfo=None)

    # Verify parent's next_occurrence was updated
    session.refresh(task)
    expected_next = due_date + timedelta(days=2)
    assert task.next_occurrence.replace(tzinfo=None) == expected_next.replace(tzinfo=None)


def test_generate_weekly_instance(session: Session):
    """Test generating a weekly recurring instance"""
    # Create recurring task (weekly on Monday)
    due_date = datetime(2026, 1, 12, 9, 0, tzinfo=pytz.UTC)  # Monday
    next_monday = due_date + timedelta(days=7)

    task = Task(
        user_id="test_user",
        title="Weekly meeting",
        due_date=due_date,
        recurring_pattern="weekly",
        recurring_interval=1,
        recurring_days=["Mon"],
        next_occurrence=next_monday
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Generate instance
    instance = generate_recurring_instances(task.id, session)

    # Verify instance was created
    assert instance is not None
    assert instance.parent_task_id == task.id
    assert instance.due_date.replace(tzinfo=None) == next_monday.replace(tzinfo=None)


def test_generate_instance_respects_end_date(session: Session):
    """Test that instance generation stops at end_date"""
    # Create recurring task with end_date in the past
    due_date = datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)
    end_date = datetime(2026, 1, 10, 9, 0, tzinfo=pytz.UTC)  # Already passed
    next_occurrence = datetime(2026, 1, 20, 9, 0, tzinfo=pytz.UTC)  # After end_date

    task = Task(
        user_id="test_user",
        title="Limited recurring task",
        due_date=due_date,
        recurring_pattern="daily",
        recurring_interval=1,
        recurring_end_date=end_date,
        next_occurrence=next_occurrence
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Attempt to generate instance should return None
    instance = generate_recurring_instances(task.id, session)
    assert instance is None


def test_generate_instance_non_recurring_task(session: Session):
    """Test that generating instance fails for non-recurring task"""
    # Create non-recurring task
    task = Task(
        user_id="test_user",
        title="Non-recurring task",
        due_date=datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Attempt to generate instance should fail
    with pytest.raises(ValueError, match="not recurring"):
        generate_recurring_instances(task.id, session)


# ============================================================================
# T089: Backfill tests
# ============================================================================

def test_backfill_1_day(session: Session):
    """Test backfilling 1 day of missed instances"""
    # Create recurring task with next_occurrence 1 day ago
    current_time = datetime.now(pytz.UTC)
    one_day_ago = current_time - timedelta(days=1)

    task = Task(
        user_id="test_user",
        title="Daily task",
        due_date=one_day_ago - timedelta(days=1),
        recurring_pattern="daily",
        recurring_interval=1,
        next_occurrence=one_day_ago
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Backfill missed instances
    instances = backfill_missed_instances(task.id, session)

    # Should create 1 instance
    assert len(instances) == 1
    assert instances[0].parent_task_id == task.id
    assert instances[0].due_date.replace(tzinfo=None) == one_day_ago.replace(tzinfo=None)


def test_backfill_7_days(session: Session):
    """Test backfilling 7 days of missed instances"""
    # Create recurring task with next_occurrence 7 days ago
    current_time = datetime.now(pytz.UTC)
    seven_days_ago = current_time - timedelta(days=7)

    task = Task(
        user_id="test_user",
        title="Daily task",
        due_date=seven_days_ago - timedelta(days=1),
        recurring_pattern="daily",
        recurring_interval=1,
        next_occurrence=seven_days_ago
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Backfill missed instances
    instances = backfill_missed_instances(task.id, session)

    # Should create 7 instances (one for each day)
    assert len(instances) >= 7


def test_backfill_no_duplicates(session: Session):
    """Test that backfill doesn't create duplicate instances"""
    # Create recurring task
    current_time = datetime.now(pytz.UTC)
    two_days_ago = current_time - timedelta(days=2)

    task = Task(
        user_id="test_user",
        title="Daily task",
        due_date=two_days_ago - timedelta(days=1),
        recurring_pattern="daily",
        recurring_interval=1,
        next_occurrence=two_days_ago
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Manually create instance for 2 days ago
    existing_instance = Task(
        user_id="test_user",
        title="Daily task",
        due_date=two_days_ago,
        parent_task_id=task.id
    )
    session.add(existing_instance)
    session.commit()

    # Backfill should not create duplicate
    instances = backfill_missed_instances(task.id, session)

    # Should create 1 instance (for yesterday), not 2
    assert len(instances) == 1
    assert instances[0].due_date != two_days_ago


def test_backfill_beyond_7_days(session: Session):
    """Test that backfill doesn't create instances older than 7 days"""
    # Create recurring task with next_occurrence 10 days ago
    current_time = datetime.now(pytz.UTC)
    ten_days_ago = current_time - timedelta(days=10)

    task = Task(
        user_id="test_user",
        title="Daily task",
        due_date=ten_days_ago - timedelta(days=1),
        recurring_pattern="daily",
        recurring_interval=1,
        next_occurrence=ten_days_ago
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Backfill missed instances
    instances = backfill_missed_instances(task.id, session)

    # Should only create instances within 7-day window
    seven_days_ago = current_time - timedelta(days=7)
    for instance in instances:
        # Truncate microseconds for comparison
        assert instance.due_date.replace(tzinfo=pytz.UTC, microsecond=0) >= seven_days_ago.replace(microsecond=0)


# ============================================================================
# T090: Next occurrence calculation tests
# ============================================================================

def test_next_occurrence_daily(session: Session):
    """Test next occurrence calculation for daily pattern"""
    start_date = datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)

    next_occ = generate_next_occurrence(
        pattern="daily",
        interval=1,
        days=None,
        start_date=start_date,
        end_date=None,
        count=1,
        timezone_str="UTC"
    )

    expected = start_date + timedelta(days=1)
    assert next_occ == expected


def test_next_occurrence_weekly_specific_days(session: Session):
    """Test next occurrence for weekly pattern with specific days"""
    # Monday at 9 AM
    monday = datetime(2026, 1, 12, 9, 0, tzinfo=pytz.UTC)

    # Weekly pattern on Mon, Wed, Fri
    next_occ = generate_next_occurrence(
        pattern="weekly",
        interval=1,
        days=["Mon", "Wed", "Fri"],
        start_date=monday,
        end_date=None,
        count=1,
        timezone_str="UTC"
    )

    # Next should be Wednesday (2 days after Monday)
    expected = monday + timedelta(days=2)
    assert next_occ == expected


def test_next_occurrence_respects_end_date(session: Session):
    """Test that next occurrence respects end_date"""
    start_date = datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)
    end_date = datetime(2026, 1, 14, 9, 0, tzinfo=pytz.UTC)  # Before start

    next_occ = generate_next_occurrence(
        pattern="daily",
        interval=1,
        days=None,
        start_date=start_date,
        end_date=end_date,
        count=1,
        timezone_str="UTC"
    )

    # Should return None (no more occurrences after end_date)
    assert next_occ is None


def test_next_occurrence_every_2_days(session: Session):
    """Test next occurrence with interval > 1"""
    start_date = datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)

    next_occ = generate_next_occurrence(
        pattern="daily",
        interval=2,
        days=None,
        start_date=start_date,
        end_date=None,
        count=1,
        timezone_str="UTC"
    )

    expected = start_date + timedelta(days=2)
    assert next_occ == expected


# ============================================================================
# Delete/Remove pattern tests
# ============================================================================

def test_remove_recurring_pattern_this_only(session: Session):
    """Test removing recurring pattern (this_only option)"""
    # Create recurring task
    task = Task(
        user_id="test_user",
        title="Recurring task",
        due_date=datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC),
        recurring_pattern="daily",
        recurring_interval=1,
        next_occurrence=datetime(2026, 1, 16, 9, 0, tzinfo=pytz.UTC)
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Remove recurring pattern (this_only)
    remove_recurring_pattern(
        task_id=task.id,
        delete_type="this_only",
        user_id="test_user",
        session=session
    )

    # Verify pattern was removed
    session.refresh(task)
    assert task.recurring_pattern is None
    assert task.next_occurrence is None


def test_remove_recurring_pattern_this_and_future(session: Session):
    """Test removing recurring pattern (this_and_future option)"""
    # Create recurring task
    due_date = datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC)
    task = Task(
        user_id="test_user",
        title="Recurring task",
        due_date=due_date,
        recurring_pattern="daily",
        recurring_interval=1,
        next_occurrence=due_date + timedelta(days=1)
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Create some future instances
    future1 = Task(
        user_id="test_user",
        title="Instance 1",
        due_date=due_date + timedelta(days=1),
        parent_task_id=task.id
    )
    future2 = Task(
        user_id="test_user",
        title="Instance 2",
        due_date=due_date + timedelta(days=2),
        parent_task_id=task.id
    )
    session.add(future1)
    session.add(future2)
    session.commit()

    # Remove recurring pattern (this_and_future)
    remove_recurring_pattern(
        task_id=task.id,
        delete_type="this_and_future",
        user_id="test_user",
        session=session
    )

    # Verify pattern was removed and future instances deleted
    session.refresh(task)
    assert task.recurring_pattern is None

    # Check instances were deleted
    instances = get_task_instances(task.id, session)
    assert len(instances) == 0


def test_remove_recurring_pattern_all(session: Session):
    """Test removing recurring pattern (all option)"""
    # Create recurring task
    task = Task(
        user_id="test_user",
        title="Recurring task",
        due_date=datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC),
        recurring_pattern="daily",
        recurring_interval=1
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    task_id = task.id

    # Create some instances
    instance1 = Task(
        user_id="test_user",
        title="Instance 1",
        parent_task_id=task.id
    )
    instance2 = Task(
        user_id="test_user",
        title="Instance 2",
        parent_task_id=task.id
    )
    session.add(instance1)
    session.add(instance2)
    session.commit()

    # Remove recurring pattern (all)
    remove_recurring_pattern(
        task_id=task_id,
        delete_type="all",
        user_id="test_user",
        session=session
    )

    # Verify parent and all instances were deleted
    remaining_task = session.get(Task, task_id)
    assert remaining_task is None

    instances = get_task_instances(task_id, session)
    assert len(instances) == 0


# ============================================================================
# Integration tests
# ============================================================================

def test_get_recurring_tasks_due(session: Session):
    """Test getting recurring tasks that are due for instance generation"""
    # Create recurring task with next_occurrence in the past
    current_time = datetime.now(pytz.UTC)
    past_occurrence = current_time - timedelta(minutes=5)

    task = Task(
        user_id="test_user",
        title="Due task",
        due_date=past_occurrence - timedelta(days=1),
        recurring_pattern="daily",
        recurring_interval=1,
        next_occurrence=past_occurrence
    )
    session.add(task)
    session.commit()

    # Get tasks due
    tasks_due = get_recurring_tasks_due(session)

    # Should include our task
    assert len(tasks_due) >= 1
    assert task.id in [t.id for t in tasks_due]


def test_get_task_instances(session: Session):
    """Test getting all instances of a recurring task"""
    # Create parent task
    task = Task(
        user_id="test_user",
        title="Parent task",
        recurring_pattern="daily"
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    # Create instances
    instance1 = Task(
        user_id="test_user",
        title="Instance 1",
        due_date=datetime(2026, 1, 15, 9, 0, tzinfo=pytz.UTC),
        parent_task_id=task.id
    )
    instance2 = Task(
        user_id="test_user",
        title="Instance 2",
        due_date=datetime(2026, 1, 16, 9, 0, tzinfo=pytz.UTC),
        parent_task_id=task.id
    )
    session.add(instance1)
    session.add(instance2)
    session.commit()

    # Get instances
    instances = get_task_instances(task.id, session)

    # Should return both instances, ordered by due_date
    assert len(instances) == 2
    assert instances[0].due_date < instances[1].due_date
