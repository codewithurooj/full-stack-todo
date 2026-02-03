"""Due date management API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from datetime import datetime
from typing import Optional
import logging
from pydantic import BaseModel

from app.database import get_session
from app.models.task import Task, TaskRead
from app.middleware.auth import get_current_user_id
from app.utils.timezone import convert_to_utc, is_valid_timezone
from app.utils.date_parser import parse_flexible_date

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/{user_id}/tasks/{task_id}", tags=["due-dates"])


class DueDateRequest(BaseModel):
    """Request model for setting due date"""
    due_date: str  # ISO 8601 date string or natural language
    timezone: str = "UTC"  # IANA timezone name


@router.put("/due-date", response_model=TaskRead)
async def set_due_date(
    user_id: str,
    task_id: int,
    due_date_request: DueDateRequest,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Set or update due date for a task.

    Args:
        user_id: User ID from path parameter
        task_id: Task ID to update
        due_date_request: Due date and timezone
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Returns:
        Updated task with due_date set

    Raises:
        HTTPException: If unauthorized, task not found, or invalid date format
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    # Get task
    db_task = session.get(Task, task_id)

    # Check if task exists and belongs to user
    if not db_task or db_task.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Validate timezone
    if not is_valid_timezone(due_date_request.timezone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timezone: {due_date_request.timezone}"
        )

    # Parse due date
    try:
        # Try flexible date parsing first (supports natural language)
        local_dt = parse_flexible_date(
            due_date_request.due_date,
            timezone_str=due_date_request.timezone
        )

        # Convert to UTC for storage
        utc_dt = convert_to_utc(local_dt, due_date_request.timezone)

        # Update task
        db_task.due_date = utc_dt
        db_task.updated_at = datetime.utcnow()

        session.add(db_task)
        session.commit()
        session.refresh(db_task)

        logger.info(
            f"set_due_date: user={user_id}, task_id={task_id}, "
            f"due_date={utc_dt.isoformat()}"
        )

        return db_task

    except ValueError as e:
        logger.warning(
            f"set_due_date validation error: user={user_id}, task_id={task_id}, "
            f"due_date={due_date_request.due_date}, error={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        logger.error(
            f"set_due_date error: user={user_id}, task_id={task_id}, error={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set due date"
        )


@router.delete("/due-date", status_code=status.HTTP_204_NO_CONTENT)
async def clear_due_date(
    user_id: str,
    task_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Clear due date from a task.

    Args:
        user_id: User ID from path parameter
        task_id: Task ID to update
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Raises:
        HTTPException: If unauthorized or task not found
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    # Get task
    db_task = session.get(Task, task_id)

    # Check if task exists and belongs to user
    if not db_task or db_task.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Clear due date
    db_task.due_date = None
    db_task.updated_at = datetime.utcnow()

    session.add(db_task)
    session.commit()

    logger.info(f"clear_due_date: user={user_id}, task_id={task_id}")
