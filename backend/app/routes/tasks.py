"""Task CRUD API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from datetime import datetime, timezone
from typing import Optional, List
import logging

from app.database import get_session
from app.models.task import Task, TaskCreate, TaskUpdate, TaskRead
from app.middleware.auth import get_current_user_id
from app.utils.query_builder import build_tasks_query
from app.utils.validation import validate_priority, validate_tags, validate_date_range
from app.config import settings
from pydantic import BaseModel

# Setup logger
logger = logging.getLogger(__name__)


async def schedule_reminders_if_due_date(task: Task, user_id: str) -> None:
    """
    Schedule reminders for a task if it has a due date and Dapr is enabled.

    Args:
        task: Task with potential due_date
        user_id: User who owns the task
    """
    if not settings.DAPR_ENABLED:
        return

    if task.due_date:
        try:
            from app.services.reminder_scheduler import get_reminder_scheduler
            scheduler = get_reminder_scheduler()
            # Ensure due_date is timezone aware
            due_date = task.due_date
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)
            await scheduler.schedule_task_reminders(
                task_id=task.id,
                user_id=user_id,
                title=task.title,
                due_date=due_date
            )
            logger.info(f"Scheduled reminders for task {task.id} with due date {due_date}")
        except Exception as e:
            logger.warning(f"Failed to schedule reminders for task {task.id}: {e}")


async def cancel_reminders(task_id: int) -> None:
    """
    Cancel reminders for a task if Dapr is enabled.

    Args:
        task_id: Task ID to cancel reminders for
    """
    if not settings.DAPR_ENABLED:
        return

    try:
        from app.services.reminder_scheduler import get_reminder_scheduler
        scheduler = get_reminder_scheduler()
        await scheduler.cancel_task_reminders(task_id)
        logger.info(f"Cancelled reminders for task {task_id}")
    except Exception as e:
        logger.warning(f"Failed to cancel reminders for task {task_id}: {e}")

router = APIRouter(prefix="/api/{user_id}/tasks", tags=["tasks"])


class TaskListResponse(BaseModel):
    """Response model for list tasks with filters applied"""
    tasks: List[TaskRead]
    count: int
    filters_applied: dict


class TagsResponse(BaseModel):
    """Response model for tags endpoint"""
    tags: List[str]
    usage_count: dict


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    user_id: str,
    priority: Optional[str] = Query(None, regex="^(high|medium|low)$"),
    tags: Optional[List[str]] = Query(None),
    status: Optional[str] = Query("all", regex="^(all|pending|completed)$"),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at", regex="^(priority|created_at|title|due_date)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    due_date_from: Optional[str] = Query(None),
    due_date_to: Optional[str] = Query(None),
    relative_range: Optional[str] = Query(None, regex="^(today|this_week|this_month|overdue)$"),
    user_timezone: str = Query("UTC"),
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    List all tasks for the authenticated user with filtering and sorting.

    Args:
        user_id: User ID from path parameter
        priority: Filter by priority (high|medium|low)
        tags: Filter by tags (can specify multiple)
        status: Filter by status (all|pending|completed)
        search: Search keyword for title/description
        sort_by: Sort field (priority|created_at|title|due_date)
        sort_order: Sort order (asc|desc)
        date_from: Filter tasks created from this date
        date_to: Filter tasks created until this date
        due_date_from: Filter tasks due from this date (ISO 8601)
        due_date_to: Filter tasks due until this date (ISO 8601)
        relative_range: Filter by relative date range (today|this_week|this_month|overdue)
        user_timezone: User's IANA timezone for relative date calculations (default: UTC)
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Returns:
        TaskListResponse with filtered tasks, count, and filters_applied

    Raises:
        HTTPException: If user_id doesn't match JWT token
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to user's tasks"
        )

    # Validate inputs
    try:
        if priority:
            validate_priority(priority)
        if tags:
            validate_tags(tags)
        if date_from or date_to:
            validate_date_range(date_from, date_to)
    except HTTPException as e:
        logger.warning(
            f"list_tasks validation error: user={user_id}, "
            f"priority={priority}, tags={tags}, date_from={date_from}, date_to={date_to}, "
            f"error={e.detail}"
        )
        raise

    # Build query with filters and sorting
    query = build_tasks_query(
        user_id=user_id,
        priority=priority,
        tags=tags,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        date_from=date_from,
        date_to=date_to,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        relative_range=relative_range,
        user_timezone=user_timezone
    )

    # Execute query
    tasks = session.exec(query).all()

    # Build filters_applied dict
    filters_applied = {}
    if priority:
        filters_applied["priority"] = priority
    if tags:
        filters_applied["tags"] = tags
    if status and status != "all":
        filters_applied["status"] = status
    if search:
        filters_applied["search"] = search
    if sort_by != "created_at" or sort_order != "desc":
        filters_applied["sort_by"] = sort_by
        filters_applied["sort_order"] = sort_order
    if date_from:
        filters_applied["date_from"] = date_from
    if date_to:
        filters_applied["date_to"] = date_to
    if due_date_from:
        filters_applied["due_date_from"] = due_date_from
    if due_date_to:
        filters_applied["due_date_to"] = due_date_to
    if relative_range:
        filters_applied["relative_range"] = relative_range

    # Log filter/search/sort operation
    logger.info(
        f"list_tasks: user={user_id}, filters={filters_applied}, "
        f"result_count={len(tasks)}"
    )

    return TaskListResponse(
        tasks=tasks,
        count=len(tasks),
        filters_applied=filters_applied
    )


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    user_id: str,
    task: TaskCreate,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Create a new task for the authenticated user.

    Args:
        user_id: User ID from path parameter
        task: Task data to create
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Returns:
        Created task

    Raises:
        HTTPException: If user_id doesn't match JWT token
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    # Validate inputs
    try:
        if task.priority:
            validate_priority(task.priority)
        if task.tags:
            validate_tags(task.tags)
    except HTTPException as e:
        logger.warning(
            f"create_task validation error: user={user_id}, "
            f"priority={task.priority}, tags={task.tags}, error={e.detail}"
        )
        raise

    # Create task
    db_task = Task(**task.model_dump(), user_id=user_id)
    session.add(db_task)
    session.commit()
    session.refresh(db_task)

    # Schedule reminders if task has due date (T039)
    await schedule_reminders_if_due_date(db_task, user_id)

    logger.info(
        f"create_task: user={user_id}, task_id={db_task.id}, "
        f"priority={db_task.priority}, tags_count={len(db_task.tags)}"
    )

    return db_task


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    user_id: str,
    task_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Get a specific task by ID.

    Args:
        user_id: User ID from path parameter
        task_id: Task ID to retrieve
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Returns:
        Task details

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
    task = session.get(Task, task_id)

    # Check if task exists and belongs to user
    if not task or task.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    user_id: str,
    task_id: int,
    task_update: TaskUpdate,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Update a task.

    Args:
        user_id: User ID from path parameter
        task_id: Task ID to update
        task_update: Updated task data
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Returns:
        Updated task

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

    # Validate inputs
    update_data = task_update.model_dump(exclude_unset=True)
    try:
        if "priority" in update_data and update_data["priority"] is not None:
            validate_priority(update_data["priority"])
        if "tags" in update_data and update_data["tags"] is not None:
            validate_tags(update_data["tags"])
    except HTTPException as e:
        logger.warning(
            f"update_task validation error: user={user_id}, task_id={task_id}, "
            f"update_data={update_data}, error={e.detail}"
        )
        raise

    # Track if due_date changed for reminder rescheduling
    old_due_date = db_task.due_date

    # Update task fields
    for field, value in update_data.items():
        setattr(db_task, field, value)

    # Update timestamp
    db_task.updated_at = datetime.utcnow()

    session.add(db_task)
    session.commit()
    session.refresh(db_task)

    # Reschedule reminders if due_date changed (T040)
    if "due_date" in update_data:
        new_due_date = db_task.due_date
        if new_due_date != old_due_date:
            if new_due_date is None:
                # Due date removed - cancel reminders
                await cancel_reminders(task_id)
            else:
                # Due date changed - reschedule reminders
                try:
                    from app.services.reminder_scheduler import get_reminder_scheduler
                    scheduler = get_reminder_scheduler()
                    due_date = new_due_date
                    if due_date.tzinfo is None:
                        due_date = due_date.replace(tzinfo=timezone.utc)
                    await scheduler.reschedule_task_reminders(
                        task_id=task_id,
                        user_id=user_id,
                        title=db_task.title,
                        new_due_date=due_date
                    )
                    logger.info(f"Rescheduled reminders for task {task_id} to {due_date}")
                except Exception as e:
                    logger.warning(f"Failed to reschedule reminders for task {task_id}: {e}")

    logger.info(
        f"update_task: user={user_id}, task_id={task_id}, "
        f"updated_fields={list(update_data.keys())}"
    )

    return db_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    user_id: str,
    task_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Delete a task.

    Args:
        user_id: User ID from path parameter
        task_id: Task ID to delete
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
    task = session.get(Task, task_id)

    # Check if task exists and belongs to user
    if not task or task.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Cancel any scheduled reminders before deleting (T041)
    await cancel_reminders(task_id)

    # Delete task
    session.delete(task)
    session.commit()


@router.patch("/{task_id}/complete", response_model=TaskRead)
async def toggle_complete(
    user_id: str,
    task_id: int,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Toggle task completion status.

    Args:
        user_id: User ID from path parameter
        task_id: Task ID to toggle
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Returns:
        Updated task

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

    # Toggle completion
    db_task.completed = not db_task.completed
    db_task.updated_at = datetime.utcnow()

    session.add(db_task)
    session.commit()
    session.refresh(db_task)

    # Cancel or reschedule reminders based on completion status (T041)
    if db_task.completed:
        # Task completed - cancel reminders
        await cancel_reminders(task_id)
    else:
        # Task uncompleted - reschedule reminders if has due date
        await schedule_reminders_if_due_date(db_task, user_id)

    # If task is now completed and has recurring pattern, generate next instance
    if db_task.completed and db_task.recurring_pattern and db_task.recurring_pattern != 'none':
        try:
            from app.services.recurring_service import generate_recurring_instances
            next_instance = generate_recurring_instances(db_task.id, session)
            if next_instance:
                logger.info(
                    f"Generated next recurring instance {next_instance.id} "
                    f"after completing task {db_task.id}"
                )
        except Exception as e:
            logger.error(
                f"Failed to generate recurring instance after completion: {e}",
                exc_info=True
            )
            # Don't fail the completion operation if instance generation fails

    return db_task


@router.get("/tags", response_model=TagsResponse)
async def get_tags(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    session: Session = Depends(get_session)
):
    """
    Get all unique tags used by the user with usage counts.

    Args:
        user_id: User ID from path parameter
        current_user_id: Authenticated user ID from JWT token
        session: Database session

    Returns:
        TagsResponse with sorted tags and usage counts

    Raises:
        HTTPException: If unauthorized
    """
    # Verify user_id matches JWT
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access"
        )

    # Get all tasks for user
    statement = select(Task).where(Task.user_id == user_id)
    tasks = session.exec(statement).all()

    # Collect all tags and count usage
    tag_counts = {}
    for task in tasks:
        for tag in task.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # Sort tags alphabetically
    sorted_tags = sorted(tag_counts.keys())

    return TagsResponse(
        tags=sorted_tags,
        usage_count=tag_counts
    )
