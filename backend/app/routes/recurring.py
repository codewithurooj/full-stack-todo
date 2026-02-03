"""Recurring task API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
import logging

from app.database import get_session
from app.models.task import TaskRead
from app.middleware.auth import get_current_user_id
from app.services import recurring_service
from app.utils.rrule import generate_next_occurrence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/{user_id}/tasks", tags=["recurring"])


class SetRecurringPatternRequest(BaseModel):
    """Request model for setting recurring pattern"""
    pattern: str  # 'daily', 'weekly', 'monthly', 'custom'
    interval: int = 1
    days: Optional[List[str]] = None  # ['Mon', 'Wed', 'Fri'] for weekly
    end_date: Optional[datetime] = None


class NextOccurrenceResponse(BaseModel):
    """Response model for next occurrence calculation"""
    next_occurrence: Optional[datetime]


class DeleteRecurringRequest(BaseModel):
    """Request model for deleting recurring pattern"""
    delete_type: str = 'this_only'  # 'this_only', 'this_and_future', 'all'


@router.put("/{task_id}/recurring", response_model=TaskRead)
async def set_recurring_pattern(
    user_id: str,
    task_id: int,
    request: SetRecurringPatternRequest,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Create or update recurring pattern on a task.

    Args:
        user_id: User ID from path parameter
        task_id: Task ID to make recurring
        request: Recurring pattern configuration
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Returns:
        Updated task with recurring pattern

    Raises:
        HTTPException: If unauthorized, task not found, or invalid pattern
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    try:
        task = recurring_service.set_recurring_pattern(
            task_id=task_id,
            pattern=request.pattern,
            interval=request.interval,
            days=request.days,
            end_date=request.end_date,
            user_id=user_id,
            session=session
        )

        logger.info(
            f"set_recurring_pattern: user={user_id}, task_id={task_id}, "
            f"pattern={request.pattern}, interval={request.interval}"
        )

        return task

    except ValueError as e:
        logger.warning(f"set_recurring_pattern validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"set_recurring_pattern error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set recurring pattern"
        )


@router.delete("/{task_id}/recurring", status_code=status.HTTP_204_NO_CONTENT)
async def remove_recurring_pattern(
    user_id: str,
    task_id: int,
    delete_type: str = Query('this_only', regex="^(this_only|this_and_future|all)$"),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Remove recurring pattern from a task.

    Args:
        user_id: User ID from path parameter
        task_id: Task ID to remove recurring pattern from
        delete_type: 'this_only' (default) | 'this_and_future' | 'all'
            - 'this_only': Set recurring_pattern=None on this task only
            - 'this_and_future': Delete all future instances (where due_date >= this.due_date)
            - 'all': Delete parent + all instances
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

    try:
        recurring_service.remove_recurring_pattern(
            task_id=task_id,
            delete_type=delete_type,
            user_id=user_id,
            session=session
        )

        logger.info(
            f"remove_recurring_pattern: user={user_id}, task_id={task_id}, "
            f"delete_type={delete_type}"
        )

    except ValueError as e:
        logger.warning(f"remove_recurring_pattern error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"remove_recurring_pattern error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove recurring pattern"
        )


@router.post("/{task_id}/next-occurrence", response_model=NextOccurrenceResponse)
async def calculate_next_occurrence(
    user_id: str,
    task_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Calculate next occurrence for a recurring task without creating instance.

    Args:
        user_id: User ID from path parameter
        task_id: Task ID to calculate next occurrence for
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Returns:
        NextOccurrenceResponse with next occurrence datetime

    Raises:
        HTTPException: If unauthorized, task not found, or not recurring
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    # Get task
    from app.models.task import Task
    task = session.get(Task, task_id)

    if not task or task.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if not task.recurring_pattern or task.recurring_pattern == 'none':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not recurring"
        )

    if not task.due_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task must have a due_date"
        )

    try:
        # Calculate next occurrence
        next_occ = generate_next_occurrence(
            pattern=task.recurring_pattern,
            interval=task.recurring_interval or 1,
            days=task.recurring_days,
            start_date=task.due_date,
            end_date=task.recurring_end_date,
            count=1,
            timezone_str="UTC"
        )

        logger.info(
            f"calculate_next_occurrence: user={user_id}, task_id={task_id}, "
            f"next={next_occ}"
        )

        return NextOccurrenceResponse(next_occurrence=next_occ)

    except Exception as e:
        logger.error(f"calculate_next_occurrence error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate next occurrence: {str(e)}"
        )
