"""Update Task tool for MCP server"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.models.task import Task
from app.mcp_server.errors import DatabaseError, NotFoundError, ValidationError
from app.mcp_server.validation import validate_user_id, validate_task_id, validate_title, validate_description
from app.mcp_server.auth import verify_user_authorization
from app.utils.date_parser import parse_flexible_date
from app.utils.timezone import convert_to_utc


class UpdateTaskRequest(BaseModel):
    """Request model for update_task tool"""
    user_id: str = Field(..., description="User identifier (must match JWT token)")
    task_id: str = Field(..., description="Task UUID to update")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="New task title (optional)")
    description: Optional[str] = Field(None, max_length=1000, description="New task description (optional)")
    priority: Optional[str] = Field(None, description="New task priority: high, medium, or low (optional)")
    tags: Optional[List[str]] = Field(None, description="New task tags (optional list, replaces existing tags)")
    due_date: Optional[str] = Field(None, description="Task due date (flexible format: 'tomorrow 9am', '2026-02-15 14:30', 'next friday')")
    timezone: Optional[str] = Field("UTC", description="User timezone for due date conversion (default: UTC)")


class UpdateTaskResponse(BaseModel):
    """Response model for update_task tool"""
    task_id: str
    title: str
    description: Optional[str]
    priority: str
    tags: List[str]
    due_date: Optional[datetime]
    updated_at: datetime


def update_task(
    request: UpdateTaskRequest,
    token_user_id: str,
    session: Session
) -> UpdateTaskResponse:
    """
    Modify task properties including title, description, priority, and tags.

    Args:
        request: UpdateTaskRequest with user_id, task_id, title, description, priority, tags
        token_user_id: User ID extracted from JWT token
        session: Database session

    Returns:
        UpdateTaskResponse with updated task details

    Raises:
        ValidationError: If input validation fails
        AuthorizationError: If user_id doesn't match token
        NotFoundError: If task not found
        DatabaseError: If database operation fails

    Notes:
        - All fields are optional; only provided fields will be updated
        - Tags replacement: Providing tags will REPLACE existing tags (not merge)
        - Priority validation: Must be "high", "medium", or "low"
    """
    # Validate inputs
    validate_user_id(request.user_id)
    validate_task_id(request.task_id)
    validate_title(request.title, required=False)
    validate_description(request.description)

    # Verify authorization
    verify_user_authorization(request.user_id, token_user_id)

    # Validate priority if provided
    if request.priority is not None:
        if request.priority.lower() not in ["high", "medium", "low"]:
            from app.mcp_server.errors import ValidationError
            raise ValidationError(
                message="Invalid priority value",
                details={"priority": request.priority, "valid_values": ["high", "medium", "low"]}
            )

    try:
        # Find task
        task = session.get(Task, int(request.task_id))

        if not task or task.user_id != request.user_id:
            raise NotFoundError(
                message="Task not found",
                details={"task_id": request.task_id}
            )

        # Update fields if provided
        if request.title is not None:
            task.title = request.title.strip()

        if request.description is not None:
            task.description = request.description.strip() if request.description else None

        if request.priority is not None:
            task.priority = request.priority.lower()

        if request.tags is not None:
            # Normalize tags (lowercase, strip whitespace, deduplicate)
            normalized_tags = sorted(list(set(tag.strip().lower() for tag in request.tags if tag.strip())))
            task.tags = normalized_tags

        # Parse and convert due date if provided
        if request.due_date is not None:
            try:
                # Parse flexible date
                parsed_dt = parse_flexible_date(
                    request.due_date,
                    timezone_str=request.timezone or "UTC"
                )
                # Convert to UTC
                task.due_date = convert_to_utc(parsed_dt, request.timezone or "UTC")
            except (ValueError, Exception) as e:
                raise ValidationError(
                    message="Invalid due date format",
                    details={"due_date": request.due_date, "error": str(e)}
                )

        task.updated_at = datetime.utcnow()

        session.add(task)
        session.commit()
        session.refresh(task)

        return UpdateTaskResponse(
            task_id=str(task.id),
            title=task.title,
            description=task.description,
            priority=task.priority,
            tags=task.tags,
            due_date=task.due_date,
            updated_at=task.updated_at
        )

    except NotFoundError:
        raise
    except Exception as e:
        session.rollback()
        raise DatabaseError(
            message="Failed to update task",
            details={"error": str(e)}
        )
