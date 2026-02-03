"""Reminder management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
import logging

from app.database import get_session
from app.middleware.auth import get_current_user_id
from app.models.reminder import Reminder, ReminderCreate, ReminderRead, ReminderSnooze
from app.services.reminder_service import (
    create_reminder,
    get_task_reminders,
    delete_reminder,
    snooze_reminder
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/{user_id}/tasks/{task_id}/reminders", tags=["reminders"])


@router.post("", response_model=ReminderRead, status_code=status.HTTP_201_CREATED)
async def create_task_reminder(
    user_id: str,
    task_id: int,
    reminder_data: ReminderCreate,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Create a reminder for a task.

    Args:
        user_id: User ID from path
        task_id: Task ID from path
        reminder_data: Reminder creation data (offset_minutes)
        current_user_id: Authenticated user ID from JWT
        session: Database session

    Returns:
        Created reminder

    Raises:
        HTTPException:
            - 400: Invalid input or task has no due_date
            - 403: Unauthorized (user_id doesn't match JWT)
            - 404: Task not found

    Example:
        POST /api/user123/tasks/456/reminders
        {
            "offset_minutes": 60,
            "task_id": 456
        }
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        logger.warning(
            f"create_task_reminder: unauthorized access. "
            f"path_user={user_id}, jwt_user={current_user_id}"
        )
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        # Create reminder
        reminder = create_reminder(
            task_id=task_id,
            user_id=user_id,
            offset_minutes=reminder_data.offset_minutes,
            session=session
        )

        if not reminder:
            logger.warning(
                f"create_task_reminder: task not found or unauthorized. "
                f"task_id={task_id}, user={user_id}"
            )
            raise HTTPException(status_code=404, detail="Task not found")

        logger.info(
            f"create_task_reminder: created. reminder_id={reminder.id}, "
            f"task_id={task_id}, user={user_id}"
        )

        return reminder

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(
            f"create_task_reminder: validation error. "
            f"task_id={task_id}, user={user_id}, error={str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"create_task_reminder: unexpected error. "
            f"task_id={task_id}, user={user_id}, error={str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=List[ReminderRead])
async def list_task_reminders(
    user_id: str,
    task_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    List all reminders for a task.

    Args:
        user_id: User ID from path
        task_id: Task ID from path
        current_user_id: Authenticated user ID from JWT
        session: Database session

    Returns:
        List of reminders for the task

    Raises:
        HTTPException:
            - 403: Unauthorized (user_id doesn't match JWT)

    Example:
        GET /api/user123/tasks/456/reminders
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        logger.warning(
            f"list_task_reminders: unauthorized access. "
            f"path_user={user_id}, jwt_user={current_user_id}"
        )
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        # Get reminders
        reminders = get_task_reminders(
            task_id=task_id,
            user_id=user_id,
            session=session
        )

        logger.info(
            f"list_task_reminders: task_id={task_id}, user={user_id}, count={len(reminders)}"
        )

        return reminders

    except Exception as e:
        logger.error(
            f"list_task_reminders: unexpected error. "
            f"task_id={task_id}, user={user_id}, error={str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_reminder(
    user_id: str,
    task_id: int,
    reminder_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Delete a reminder.

    Args:
        user_id: User ID from path
        task_id: Task ID from path (for path consistency)
        reminder_id: Reminder ID to delete
        current_user_id: Authenticated user ID from JWT
        session: Database session

    Returns:
        204 No Content

    Raises:
        HTTPException:
            - 403: Unauthorized (user_id doesn't match JWT)
            - 404: Reminder not found

    Example:
        DELETE /api/user123/tasks/456/reminders/789
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        logger.warning(
            f"delete_task_reminder: unauthorized access. "
            f"path_user={user_id}, jwt_user={current_user_id}"
        )
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        # Delete reminder
        deleted = delete_reminder(
            reminder_id=reminder_id,
            user_id=user_id,
            session=session
        )

        if not deleted:
            raise HTTPException(status_code=404, detail="Reminder not found")

        logger.info(
            f"delete_task_reminder: deleted. reminder_id={reminder_id}, "
            f"task_id={task_id}, user={user_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"delete_task_reminder: unexpected error. "
            f"reminder_id={reminder_id}, user={user_id}, error={str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{reminder_id}/snooze", response_model=ReminderRead)
async def snooze_task_reminder(
    user_id: str,
    task_id: int,
    reminder_id: int,
    snooze_data: ReminderSnooze,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Snooze a reminder (reschedule it).

    Args:
        user_id: User ID from path
        task_id: Task ID from path (for path consistency)
        reminder_id: Reminder ID to snooze
        snooze_data: Snooze data (snooze_minutes)
        current_user_id: Authenticated user ID from JWT
        session: Database session

    Returns:
        Updated reminder

    Raises:
        HTTPException:
            - 400: Invalid snooze_minutes (must be 1-1440)
            - 403: Unauthorized (user_id doesn't match JWT)
            - 404: Reminder not found

    Example:
        PATCH /api/user123/tasks/456/reminders/789/snooze
        {
            "snooze_minutes": 10
        }
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        logger.warning(
            f"snooze_task_reminder: unauthorized access. "
            f"path_user={user_id}, jwt_user={current_user_id}"
        )
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        # Snooze reminder
        reminder = snooze_reminder(
            reminder_id=reminder_id,
            user_id=user_id,
            snooze_minutes=snooze_data.snooze_minutes,
            session=session
        )

        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")

        logger.info(
            f"snooze_task_reminder: snoozed. reminder_id={reminder_id}, "
            f"task_id={task_id}, user={user_id}, snooze_minutes={snooze_data.snooze_minutes}"
        )

        return reminder

    except ValueError as e:
        logger.error(
            f"snooze_task_reminder: validation error. "
            f"reminder_id={reminder_id}, user={user_id}, error={str(e)}"
        )
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"snooze_task_reminder: unexpected error. "
            f"reminder_id={reminder_id}, user={user_id}, error={str(e)}"
        )
        raise HTTPException(status_code=500, detail="Internal server error")
