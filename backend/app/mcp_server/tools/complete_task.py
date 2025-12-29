"""Complete Task tool for MCP server"""
from datetime import datetime
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.models.task import Task
from app.mcp_server.errors import DatabaseError, NotFoundError
from app.mcp_server.validation import validate_user_id, validate_task_id
from app.mcp_server.auth import verify_user_authorization


class CompleteTaskRequest(BaseModel):
    """Request model for complete_task tool"""
    user_id: str = Field(..., description="User identifier (must match JWT token)")
    task_id: str = Field(..., description="Task UUID to toggle completion")


class CompleteTaskResponse(BaseModel):
    """Response model for complete_task tool"""
    task_id: str
    completed: bool
    updated_at: datetime


def complete_task(
    request: CompleteTaskRequest,
    token_user_id: str,
    session: Session
) -> CompleteTaskResponse:
    """
    Toggle task completion status.

    Args:
        request: CompleteTaskRequest with user_id and task_id
        token_user_id: User ID extracted from JWT token
        session: Database session

    Returns:
        CompleteTaskResponse with task_id, completed, updated_at

    Raises:
        ValidationError: If input validation fails
        AuthorizationError: If user_id doesn't match token
        NotFoundError: If task not found
        DatabaseError: If database operation fails
    """
    # Validate inputs
    validate_user_id(request.user_id)
    validate_task_id(request.task_id)

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

        # Toggle completion
        task.completed = not task.completed
        task.updated_at = datetime.utcnow()

        session.add(task)
        session.commit()
        session.refresh(task)

        return CompleteTaskResponse(
            task_id=str(task.id),
            completed=task.completed,
            updated_at=task.updated_at
        )

    except NotFoundError:
        raise
    except Exception as e:
        session.rollback()
        raise DatabaseError(
            message="Failed to toggle task completion",
            details={"error": str(e)}
        )
