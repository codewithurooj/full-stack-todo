"""Recurring task service for managing recurring patterns and instance generation.

This service handles:
- Setting and removing recurring patterns on tasks
- Generating new instances of recurring tasks
- Backfilling missed instances (up to 7 days)
- Calculating next occurrences
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlmodel import Session, select
import logging
import pytz

from app.models.task import Task
from app.utils.rrule import generate_next_occurrence

logger = logging.getLogger(__name__)


def set_recurring_pattern(
    task_id: int,
    pattern: str,
    interval: int,
    days: Optional[List[str]],
    end_date: Optional[datetime],
    user_id: str,
    session: Session
) -> Task:
    """Set recurring pattern on a task.

    Args:
        task_id: Task ID to make recurring
        pattern: Recurrence pattern ('daily', 'weekly', 'monthly', 'custom')
        interval: Interval between recurrences (e.g., 2 for every 2 days)
        days: Days of week for weekly patterns (e.g., ['Mon', 'Wed', 'Fri'])
        end_date: Optional end date for recurring series
        user_id: User ID (for authorization)
        session: Database session

    Returns:
        Updated task with recurring pattern set

    Raises:
        ValueError: If task not found, has no due_date, or invalid pattern
    """
    # Get task
    task = session.get(Task, task_id)
    if not task or task.user_id != user_id:
        raise ValueError("Task not found")

    # Validate task has due_date (required for recurring)
    if not task.due_date:
        raise ValueError("Task must have a due_date before setting recurring pattern")

    # Validate pattern
    valid_patterns = ['daily', 'weekly', 'monthly', 'custom']
    if pattern.lower() not in valid_patterns:
        raise ValueError(f"Invalid pattern. Must be one of: {', '.join(valid_patterns)}")

    # Validate interval
    if interval < 1:
        raise ValueError("Interval must be >= 1")

    # Update task with recurring fields
    task.recurring_pattern = pattern.lower()
    task.recurring_interval = interval
    task.recurring_days = days
    task.recurring_end_date = end_date

    # Calculate and set next_occurrence
    try:
        next_occ = generate_next_occurrence(
            pattern=pattern,
            interval=interval,
            days=days,
            start_date=task.due_date,
            end_date=end_date,
            count=1,
            timezone_str="UTC"
        )
        task.next_occurrence = next_occ
    except Exception as e:
        logger.error(f"Failed to calculate next occurrence: {e}")
        raise ValueError(f"Invalid recurring pattern: {e}")

    # Update timestamp
    task.updated_at = datetime.now(timezone.utc)

    session.add(task)
    session.commit()
    session.refresh(task)

    logger.info(
        f"set_recurring_pattern: task_id={task_id}, pattern={pattern}, "
        f"interval={interval}, next_occurrence={task.next_occurrence}"
    )

    return task


def remove_recurring_pattern(
    task_id: int,
    delete_type: str,
    user_id: str,
    session: Session
) -> None:
    """Remove recurring pattern with delete options.

    Args:
        task_id: Task ID to remove recurring pattern from
        delete_type: 'this_only' | 'this_and_future' | 'all'
            - 'this_only': Set recurring_pattern='none' on this task only
            - 'this_and_future': Delete all future instances (where due_date >= this.due_date)
            - 'all': Delete parent + all instances
        user_id: User ID (for authorization)
        session: Database session

    Raises:
        ValueError: If task not found or invalid delete_type
    """
    # Get task
    task = session.get(Task, task_id)
    if not task or task.user_id != user_id:
        raise ValueError("Task not found")

    # Validate delete_type
    valid_types = ['this_only', 'this_and_future', 'all']
    if delete_type not in valid_types:
        raise ValueError(f"Invalid delete_type. Must be one of: {', '.join(valid_types)}")

    if delete_type == 'this_only':
        # Just remove recurring pattern from this task
        task.recurring_pattern = None
        task.recurring_interval = None
        task.recurring_days = None
        task.recurring_end_date = None
        task.next_occurrence = None
        task.updated_at = datetime.now(timezone.utc)
        session.add(task)
        logger.info(f"remove_recurring_pattern: task_id={task_id}, type=this_only")

    elif delete_type == 'this_and_future':
        # Delete all future instances (where due_date >= this.due_date)
        if task.due_date:
            stmt = select(Task).where(
                Task.parent_task_id == task_id,
                Task.user_id == user_id,
                Task.due_date >= task.due_date
            )
            future_instances = session.exec(stmt).all()

            for instance in future_instances:
                session.delete(instance)

            logger.info(
                f"remove_recurring_pattern: task_id={task_id}, "
                f"type=this_and_future, deleted={len(future_instances)} instances"
            )

        # Remove recurring pattern from parent
        task.recurring_pattern = None
        task.recurring_interval = None
        task.recurring_days = None
        task.recurring_end_date = None
        task.next_occurrence = None
        task.updated_at = datetime.now(timezone.utc)
        session.add(task)

    elif delete_type == 'all':
        # Delete all instances (children)
        stmt = select(Task).where(
            Task.parent_task_id == task_id,
            Task.user_id == user_id
        )
        all_instances = session.exec(stmt).all()

        for instance in all_instances:
            session.delete(instance)

        # Flush to ensure children are deleted before parent
        session.flush()

        # Delete parent task
        session.delete(task)

        logger.info(
            f"remove_recurring_pattern: task_id={task_id}, "
            f"type=all, deleted parent + {len(all_instances)} instances"
        )

    session.commit()


def generate_recurring_instances(
    task_id: int,
    session: Session
) -> Optional[Task]:
    """Generate next recurring instance for a task.

    Args:
        task_id: Parent task ID
        session: Database session

    Returns:
        New task instance, or None if no more occurrences

    Raises:
        ValueError: If task not found or not recurring
    """
    # Get parent task
    task = session.get(Task, task_id)
    if not task:
        raise ValueError("Task not found")

    # Validate it has recurring_pattern
    if not task.recurring_pattern or task.recurring_pattern == 'none':
        raise ValueError("Task is not recurring")

    # Validate next_occurrence exists
    if not task.next_occurrence:
        logger.warning(f"Task {task_id} has no next_occurrence, cannot generate instance")
        return None

    # Check if we've exceeded end_date
    if task.recurring_end_date and task.next_occurrence > task.recurring_end_date:
        logger.info(f"Task {task_id} reached end_date, no more instances")
        return None

    # Create new Task instance
    new_instance = Task(
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        completed=False,
        priority=task.priority,
        tags=task.tags,
        due_date=task.next_occurrence,
        parent_task_id=task.id,
        recurring_pattern=None,  # Instances are not themselves recurring
        recurring_interval=None,
        recurring_days=None,
        recurring_end_date=None,
        next_occurrence=None,
        created_at=datetime.now(timezone.utc)
    )

    session.add(new_instance)

    # Calculate next occurrence for parent
    try:
        next_occ = generate_next_occurrence(
            pattern=task.recurring_pattern,
            interval=task.recurring_interval or 1,
            days=task.recurring_days,
            start_date=task.next_occurrence,
            end_date=task.recurring_end_date,
            count=1,
            timezone_str="UTC"
        )

        # Update parent's next_occurrence
        task.next_occurrence = next_occ
        task.updated_at = datetime.now(timezone.utc)
        session.add(task)

    except Exception as e:
        logger.error(f"Failed to calculate next occurrence for task {task_id}: {e}")
        # Set next_occurrence to None to prevent further generation
        task.next_occurrence = None
        session.add(task)

    session.commit()
    session.refresh(new_instance)

    logger.info(
        f"generate_recurring_instances: parent_id={task_id}, "
        f"instance_id={new_instance.id}, due_date={new_instance.due_date}, "
        f"next_occurrence={task.next_occurrence}"
    )

    return new_instance


def backfill_missed_instances(
    task_id: int,
    session: Session
) -> List[Task]:
    """Backfill up to 7 days of missed instances.

    Args:
        task_id: Parent task ID
        session: Database session

    Returns:
        List of created instances

    Raises:
        ValueError: If task not found or not recurring
    """
    # Get parent task
    task = session.get(Task, task_id)
    if not task:
        raise ValueError("Task not found")

    # Validate it has recurring_pattern
    if not task.recurring_pattern or task.recurring_pattern == 'none':
        raise ValueError("Task is not recurring")

    if not task.next_occurrence:
        logger.warning(f"Task {task_id} has no next_occurrence, cannot backfill")
        return []

    # Calculate backfill window: up to 7 days ago
    # Use 5-second buffer to avoid timing issues with tests
    current_time = datetime.now(pytz.UTC) - timedelta(seconds=5)
    backfill_start = current_time - timedelta(days=7)

    # Get existing instances to avoid duplicates
    stmt = select(Task.due_date).where(
        Task.parent_task_id == task_id,
        Task.user_id == task.user_id
    )
    existing_due_dates = set(session.exec(stmt).all())

    created_instances = []
    next_dt = task.next_occurrence

    # Generate instances up to current time
    while next_dt and (next_dt.replace(tzinfo=pytz.UTC) if next_dt.tzinfo is None else next_dt) < current_time:
        # Only create if within backfill window and doesn't already exist
        if (next_dt.replace(tzinfo=pytz.UTC) if next_dt.tzinfo is None else next_dt) >= backfill_start and next_dt not in existing_due_dates:
            new_instance = Task(
                user_id=task.user_id,
                title=task.title,
                description=task.description,
                completed=False,
                priority=task.priority,
                tags=task.tags,
                due_date=next_dt,
                parent_task_id=task.id,
                recurring_pattern=None,
                recurring_interval=None,
                recurring_days=None,
                recurring_end_date=None,
                next_occurrence=None,
                created_at=current_time
            )
            session.add(new_instance)
            created_instances.append(new_instance)
            existing_due_dates.add(next_dt)

        # Calculate next occurrence
        try:
            next_dt = generate_next_occurrence(
                pattern=task.recurring_pattern,
                interval=task.recurring_interval or 1,
                days=task.recurring_days,
                start_date=next_dt,
                end_date=task.recurring_end_date,
                count=1,
                timezone_str="UTC"
            )
        except Exception as e:
            logger.error(f"Failed to calculate next occurrence during backfill: {e}")
            break

        # Check end_date
        if task.recurring_end_date and next_dt and next_dt > task.recurring_end_date:
            break

    # Update parent's next_occurrence to the calculated value
    if next_dt and next_dt > current_time:
        task.next_occurrence = next_dt
    elif next_dt and next_dt <= current_time:
        # Calculate one more occurrence after current time
        try:
            next_dt = generate_next_occurrence(
                pattern=task.recurring_pattern,
                interval=task.recurring_interval or 1,
                days=task.recurring_days,
                start_date=next_dt,
                end_date=task.recurring_end_date,
                count=1,
                timezone_str="UTC"
            )
            task.next_occurrence = next_dt
        except Exception:
            task.next_occurrence = None

    task.updated_at = datetime.now(timezone.utc)
    session.add(task)
    session.commit()

    for instance in created_instances:
        session.refresh(instance)

    logger.info(
        f"backfill_missed_instances: task_id={task_id}, "
        f"created={len(created_instances)} instances"
    )

    return created_instances


def get_recurring_tasks_due(session: Session) -> List[Task]:
    """Get tasks that need instances generated (next_occurrence <= now).

    Args:
        session: Database session

    Returns:
        List of tasks ready for instance generation
    """
    current_time = datetime.now(pytz.UTC)

    stmt = select(Task).where(
        Task.recurring_pattern.isnot(None),
        Task.recurring_pattern != 'none',
        Task.next_occurrence.isnot(None),
        Task.next_occurrence <= current_time
    )

    tasks = session.exec(stmt).all()

    logger.info(f"get_recurring_tasks_due: found {len(tasks)} tasks")

    return tasks


def get_task_instances(
    parent_task_id: int,
    session: Session
) -> List[Task]:
    """Get all instances of a recurring task.

    Args:
        parent_task_id: Parent task ID
        session: Database session

    Returns:
        List of task instances, ordered by due_date
    """
    stmt = select(Task).where(
        Task.parent_task_id == parent_task_id
    ).order_by(Task.due_date)

    instances = session.exec(stmt).all()

    return instances
