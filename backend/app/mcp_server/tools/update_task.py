"""Update Task tool for MCP server"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.models.task import Task
from app.mcp_server.errors import DatabaseError, NotFoundError
from app.mcp_server.validation import validate_user_id, validate_task_id, validate_title, validate_description
from app.mcp_server.auth import verify_user_authorization


class UpdateTaskRequest(BaseModel):
    """Request model for update_task tool"""
    user_id: str = Field(..., description="User identifier (must match JWT token)")
    task_id: str = Field(..., description="Task UUID to update")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="New task title (optional)")
    description: Optional[str] = Field(None, max_length=1000, description="New task description (optional)")


class UpdateTaskResponse(BaseModel):
    """Response model for update_task tool"""
    task_id: str
    title: str
    description: Optional[str]
    updated_at: datetime


def update_task(
    request: UpdateTaskRequest,
    token_user_id: str,
    session: Session
) -> UpdateTaskResponse:
    """
    Modify task title and/or description.

    Args:
        request: UpdateTaskRequest with user_id, task_id, title, description
        token_user_id: User ID extracted from JWT token
        session: Database session

    Returns:
        UpdateTaskResponse with task_id, title, description, updated_at

    Raises:
        ValidationError: If input validation fails
        AuthorizationError: If user_id doesn't match token
        NotFoundError: If task not found
        DatabaseError: If database operation fails
    """
    # Validate inputs
    validate_user_id(request.user_id)
    validate_task_id(request.task_id)
    validate_title(request.title, required=False)
    validate_description(request.description)

    # Verify authorization
    verify_user_authorization(request.user_id, token_user_id)

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

        task.updated_at = datetime.utcnow()

        session.add(task)
        session.commit()
        session.refresh(task)

        return UpdateTaskResponse(
            task_id=str(task.id),
            title=task.title,
            description=task.description,
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
