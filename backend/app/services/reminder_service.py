"""Reminder service with business logic for reminder operations"""
from sqlmodel import Session, select
from datetime import datetime, timedelta
from typing import Optional, List
import logging

from app.models.reminder import Reminder, ReminderCreate
from app.models.task import Task

logger = logging.getLogger(__name__)


def calculate_remind_at(due_date: datetime, offset_minutes: int) -> datetime:
    """
    Calculate when to send the reminder based on due date and offset.

    Args:
        due_date: Task due date (UTC)
        offset_minutes: Minutes before due date to send reminder

    Returns:
        datetime: Absolute UTC time when reminder should trigger

    Example:
        >>> due = datetime(2026, 1, 15, 10, 0)  # 10:00 AM
        >>> remind = calculate_remind_at(due, 60)  # 1 hour before
        >>> remind
        datetime(2026, 1, 15, 9, 0)  # 9:00 AM
    """
    return due_date - timedelta(minutes=offset_minutes)


def create_reminder(
    task_id: int,
    user_id: str,
    offset_minutes: int,
    session: Session
) -> Optional[Reminder]:
    """
    Create and schedule a reminder for a task.

    Args:
        task_id: Task ID to create reminder for
        user_id: User ID for authorization
        offset_minutes: Minutes before due date to send reminder
        session: Database session

    Returns:
        Created reminder or None if task not found or has no due date

    Raises:
        ValueError: If task has no due_date or offset is invalid
    """
    # Get task
    task = session.get(Task, task_id)

    if not task or task.user_id != user_id:
        logger.warning(f"create_reminder: task not found or unauthorized. task_id={task_id}, user={user_id}")
        return None

    # Validate task has due date
    if not task.due_date:
        raise ValueError("Cannot create reminder for task without due date")

    # Validate offset
    if offset_minutes < 0:
        raise ValueError("offset_minutes must be non-negative")

    # Calculate remind_at
    remind_at = calculate_remind_at(task.due_date, offset_minutes)

    # Check if remind_at is in the past
    if remind_at < datetime.utcnow():
        logger.warning(
            f"create_reminder: remind_at is in the past. task_id={task_id}, "
            f"remind_at={remind_at.isoformat()}, now={datetime.utcnow().isoformat()}"
        )
        # Allow creation but it will be processed immediately
        pass

    # Create reminder
    reminder = Reminder(
        task_id=task_id,
        user_id=user_id,
        offset_minutes=offset_minutes,
        remind_at=remind_at,
        delivered=False,
        delivery_status="pending"
    )

    session.add(reminder)
    session.commit()
    session.refresh(reminder)

    logger.info(
        f"create_reminder: created. reminder_id={reminder.id}, task_id={task_id}, "
        f"user={user_id}, remind_at={remind_at.isoformat()}"
    )

    return reminder


def get_task_reminders(
    task_id: int,
    user_id: str,
    session: Session
) -> List[Reminder]:
    """
    Get all reminders for a task.

    Args:
        task_id: Task ID to get reminders for
        user_id: User ID for authorization
        session: Database session

    Returns:
        List of reminders for the task
    """
    statement = select(Reminder).where(
        Reminder.task_id == task_id,
        Reminder.user_id == user_id
    ).order_by(Reminder.remind_at.asc())

    reminders = session.exec(statement).all()

    logger.info(
        f"get_task_reminders: task_id={task_id}, user={user_id}, count={len(reminders)}"
    )

    return list(reminders)


def delete_reminder(
    reminder_id: int,
    user_id: str,
    session: Session
) -> bool:
    """
    Delete a reminder.

    Args:
        reminder_id: Reminder ID to delete
        user_id: User ID for authorization
        session: Database session

    Returns:
        True if deleted, False if not found or unauthorized
    """
    reminder = session.get(Reminder, reminder_id)

    if not reminder or reminder.user_id != user_id:
        logger.warning(
            f"delete_reminder: reminder not found or unauthorized. "
            f"reminder_id={reminder_id}, user={user_id}"
        )
        return False

    session.delete(reminder)
    session.commit()

    logger.info(f"delete_reminder: deleted. reminder_id={reminder_id}, user={user_id}")

    return True


def snooze_reminder(
    reminder_id: int,
    user_id: str,
    snooze_minutes: int,
    session: Session
) -> Optional[Reminder]:
    """
    Snooze a reminder (reschedule it).

    Args:
        reminder_id: Reminder ID to snooze
        user_id: User ID for authorization
        snooze_minutes: Minutes to snooze (1-1440, max 24 hours)
        session: Database session

    Returns:
        Updated reminder or None if not found

    Raises:
        ValueError: If snooze_minutes is invalid
    """
    # Validate snooze duration
    if snooze_minutes < 1 or snooze_minutes > 1440:
        raise ValueError("snooze_minutes must be between 1 and 1440 (24 hours)")

    # Get reminder
    reminder = session.get(Reminder, reminder_id)

    if not reminder or reminder.user_id != user_id:
        logger.warning(
            f"snooze_reminder: reminder not found or unauthorized. "
            f"reminder_id={reminder_id}, user={user_id}"
        )
        return None

    # Calculate new remind_at
    new_remind_at = datetime.utcnow() + timedelta(minutes=snooze_minutes)

    # Update reminder
    reminder.remind_at = new_remind_at
    reminder.delivered = False
    reminder.delivery_status = "snoozed"
    reminder.delivery_timestamp = None
    reminder.updated_at = datetime.utcnow()

    session.add(reminder)
    session.commit()
    session.refresh(reminder)

    logger.info(
        f"snooze_reminder: snoozed. reminder_id={reminder_id}, user={user_id}, "
        f"snooze_minutes={snooze_minutes}, new_remind_at={new_remind_at.isoformat()}"
    )

    return reminder


def get_pending_reminders(
    session: Session,
    current_time: Optional[datetime] = None,
    lookahead_minutes: int = 5
) -> List[Reminder]:
    """
    Get reminders that are due now (pending and remind_at <= current_time + lookahead).

    Args:
        session: Database session
        current_time: Reference time (default: now UTC)
        lookahead_minutes: How far ahead to look for reminders (default: 5)

    Returns:
        List of pending reminders
    """
    if current_time is None:
        current_time = datetime.utcnow()

    # Calculate lookahead window
    window_end = current_time + timedelta(minutes=lookahead_minutes)

    statement = select(Reminder).where(
        Reminder.delivered == False,
        Reminder.remind_at <= window_end
    ).order_by(Reminder.remind_at.asc())

    reminders = session.exec(statement).all()

    logger.info(
        f"get_pending_reminders: current_time={current_time.isoformat()}, "
        f"lookahead={lookahead_minutes}min, count={len(reminders)}"
    )

    return list(reminders)


def mark_reminder_delivered(
    reminder_id: int,
    session: Session,
    notification_id: Optional[str] = None,
    success: bool = True
) -> Optional[Reminder]:
    """
    Mark a reminder as delivered.

    Args:
        reminder_id: Reminder ID to mark
        session: Database session
        notification_id: External notification system ID (optional)
        success: Whether delivery was successful

    Returns:
        Updated reminder or None if not found
    """
    reminder = session.get(Reminder, reminder_id)

    if not reminder:
        logger.warning(f"mark_reminder_delivered: reminder not found. id={reminder_id}")
        return None

    # Update delivery status
    reminder.delivered = success
    reminder.delivery_status = "sent" if success else "failed"
    reminder.delivery_timestamp = datetime.utcnow()
    reminder.notification_id = notification_id
    reminder.updated_at = datetime.utcnow()

    session.add(reminder)
    session.commit()
    session.refresh(reminder)

    logger.info(
        f"mark_reminder_delivered: reminder_id={reminder_id}, success={success}, "
        f"status={reminder.delivery_status}"
    )

    return reminder


def get_failed_reminders(
    session: Session,
    max_retries: int = 3
) -> List[Reminder]:
    """
    Get reminders that failed to deliver and should be retried.

    Args:
        session: Database session
        max_retries: Maximum number of retry attempts

    Returns:
        List of failed reminders to retry
    """
    # For MVP, we'll just return failed reminders
    # In production, you'd track retry count in the model
    statement = select(Reminder).where(
        Reminder.delivery_status == "failed",
        Reminder.delivered == False
    ).order_by(Reminder.remind_at.asc())

    reminders = session.exec(statement).all()

    logger.info(f"get_failed_reminders: count={len(reminders)}")

    return list(reminders)
