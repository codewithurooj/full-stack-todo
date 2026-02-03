"""Task service with business logic for task operations"""
from sqlmodel import Session, select
from datetime import datetime
from typing import Optional, List
import logging

from app.models.task import Task
from app.utils.timezone import convert_to_utc
from app.utils.date_parser import parse_flexible_date

logger = logging.getLogger(__name__)


def update_task_due_date(
    task_id: int,
    user_id: str,
    due_date_iso: str,
    timezone: str,
    session: Session
) -> Optional[Task]:
    """
    Update task due date with timezone conversion.

    Args:
        task_id: Task ID to update
        user_id: User ID for authorization
        due_date_iso: ISO 8601 date string or natural language
        timezone: IANA timezone name
        session: Database session

    Returns:
        Updated task or None if not found

    Raises:
        ValueError: If date format is invalid or timezone is invalid
    """
    # Get task
    task = session.get(Task, task_id)

    if not task or task.user_id != user_id:
        return None

    # Parse and convert date
    try:
        local_dt = parse_flexible_date(due_date_iso, timezone_str=timezone)
        utc_dt = convert_to_utc(local_dt, timezone)

        # Update task
        task.due_date = utc_dt
        task.updated_at = datetime.utcnow()

        session.add(task)
        session.commit()
        session.refresh(task)

        logger.info(
            f"update_task_due_date: task_id={task_id}, user={user_id}, "
            f"due_date={utc_dt.isoformat()}"
        )

        return task
    except Exception as e:
        logger.error(
            f"update_task_due_date error: task_id={task_id}, error={str(e)}"
        )
        raise ValueError(f"Failed to update due date: {str(e)}")


def clear_task_due_date(
    task_id: int,
    user_id: str,
    session: Session
) -> Optional[Task]:
    """
    Clear due date from task.

    Args:
        task_id: Task ID to update
        user_id: User ID for authorization
        session: Database session

    Returns:
        Updated task or None if not found
    """
    # Get task
    task = session.get(Task, task_id)

    if not task or task.user_id != user_id:
        return None

    # Clear due date
    task.due_date = None
    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)

    logger.info(f"clear_task_due_date: task_id={task_id}, user={user_id}")

    return task


def get_tasks_by_due_date_range(
    user_id: str,
    start_date: datetime,
    end_date: datetime,
    session: Session
) -> List[Task]:
    """
    Get tasks with due dates in the specified range.

    Args:
        user_id: User ID to filter tasks
        start_date: Start of date range (timezone-aware)
        end_date: End of date range (timezone-aware)
        session: Database session

    Returns:
        List of tasks with due dates in range
    """
    statement = select(Task).where(
        Task.user_id == user_id,
        Task.due_date >= start_date,
        Task.due_date <= end_date
    ).order_by(Task.due_date.asc())

    tasks = session.exec(statement).all()

    logger.info(
        f"get_tasks_by_due_date_range: user={user_id}, "
        f"start={start_date.isoformat()}, end={end_date.isoformat()}, "
        f"count={len(tasks)}"
    )

    return tasks


def get_overdue_tasks(
    user_id: str,
    reference_time: Optional[datetime] = None,
    session: Session = None
) -> List[Task]:
    """
    Get overdue tasks (due date in the past and not completed).

    Args:
        user_id: User ID to filter tasks
        reference_time: Time to compare against (default: current UTC time)
        session: Database session

    Returns:
        List of overdue tasks
    """
    if reference_time is None:
        reference_time = datetime.utcnow()

    statement = select(Task).where(
        Task.user_id == user_id,
        Task.due_date < reference_time,
        Task.completed == False
    ).order_by(Task.due_date.asc())

    tasks = session.exec(statement).all()

    logger.info(
        f"get_overdue_tasks: user={user_id}, count={len(tasks)}"
    )

    return tasks


def get_upcoming_tasks(
    user_id: str,
    days_ahead: int = 7,
    session: Session = None
) -> List[Task]:
    """
    Get upcoming tasks due in the next N days.

    Args:
        user_id: User ID to filter tasks
        days_ahead: Number of days to look ahead (default: 7)
        session: Database session

    Returns:
        List of upcoming tasks
    """
    from datetime import timedelta

    now = datetime.utcnow()
    end_date = now + timedelta(days=days_ahead)

    statement = select(Task).where(
        Task.user_id == user_id,
        Task.due_date >= now,
        Task.due_date <= end_date,
        Task.completed == False
    ).order_by(Task.due_date.asc())

    tasks = session.exec(statement).all()

    logger.info(
        f"get_upcoming_tasks: user={user_id}, days={days_ahead}, count={len(tasks)}"
    )

    return tasks
