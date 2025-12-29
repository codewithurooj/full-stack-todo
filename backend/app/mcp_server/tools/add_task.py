"""Add Task tool for MCP server"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.models.task import Task
from app.mcp_server.errors import DatabaseError
from app.mcp_server.validation import validate_user_id, validate_title, validate_description
from app.mcp_server.auth import verify_user_authorization


class AddTaskRequest(BaseModel):
    """Request model for add_task tool"""
    user_id: str = Field(..., description="User identifier (must match JWT token)")
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Optional task description")


class AddTaskResponse(BaseModel):
    """Response model for add_task tool"""
    task_id: str
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime
    updated_at: datetime


def add_task(
    request: AddTaskRequest,
    token_user_id: str,
    session: Session
) -> AddTaskResponse:
    """
    Create a new task for the authenticated user.

    Args:
        request: AddTaskRequest with user_id, title, description
        token_user_id: User ID extracted from JWT token
        session: Database session

    Returns:
        AddTaskResponse with created task details

    Raises:
        ValidationError: If input validation fails
        AuthorizationError: If user_id doesn't match token
        DatabaseError: If database operation fails
    """
    # Validate inputs
    validate_user_id(request.user_id)
    validate_title(request.title, required=True)
    validate_description(request.description)

    # Verify authorization
    verify_user_authorization(request.user_id, token_user_id)

    try:
        # Create task
        db_task = Task(
            user_id=request.user_id,
            title=request.title.strip(),
            description=request.description.strip() if request.description else None,
            completed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        session.add(db_task)
        session.commit()
        session.refresh(db_task)

        # Return response
        return AddTaskResponse(
            task_id=str(db_task.id),
            title=db_task.title,
            description=db_task.description,
            completed=db_task.completed,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at
        )

    except Exception as e:
        session.rollback()
        raise DatabaseError(
            message="Failed to create task",
            details={"error": str(e)}
        )
