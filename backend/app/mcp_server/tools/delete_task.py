"""Delete Task tool for MCP server"""
from datetime import datetime
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.models.task import Task
from app.mcp_server.errors import DatabaseError, NotFoundError
from app.mcp_server.validation import validate_user_id, validate_task_id
from app.mcp_server.auth import verify_user_authorization


class DeleteTaskRequest(BaseModel):
    """Request model for delete_task tool"""
    user_id: str = Field(..., description="User identifier (must match JWT token)")
    task_id: str = Field(..., description="Task UUID to delete")


class DeleteTaskResponse(BaseModel):
    """Response model for delete_task tool"""
    task_id: str
    deleted: bool = True
    deleted_at: datetime


def delete_task(
    request: DeleteTaskRequest,
    token_user_id: str,
    session: Session
) -> DeleteTaskResponse:
    """
    Permanently delete a task.

    Args:
        request: DeleteTaskRequest with user_id and task_id
        token_user_id: User ID extracted from JWT token
        session: Database session

    Returns:
        DeleteTaskResponse with task_id, deleted, deleted_at

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

        # Store task_id before deletion
        task_id = str(task.id)
        deleted_at = datetime.utcnow()

        # Delete task
        session.delete(task)
        session.commit()

        return DeleteTaskResponse(
            task_id=task_id,
            deleted=True,
            deleted_at=deleted_at
        )

    except NotFoundError:
        raise
    except Exception as e:
        session.rollback()
        raise DatabaseError(
            message="Failed to delete task",
            details={"error": str(e)}
        )
