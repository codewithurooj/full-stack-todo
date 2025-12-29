"""List Tasks tool for MCP server"""
from typing import Optional, Literal, List
from datetime import datetime
from pydantic import BaseModel, Field
from sqlmodel import Session, select, col
from app.models.task import Task
from app.mcp_server.errors import DatabaseError
from app.mcp_server.validation import validate_user_id
from app.mcp_server.auth import verify_user_authorization


class ListTasksRequest(BaseModel):
    """Request model for list_tasks tool"""
    user_id: str = Field(..., description="User identifier (must match JWT token)")
    filter: Literal["all", "pending", "completed"] = Field(
        default="all",
        description="Filter tasks by completion status"
    )
    sort_by: Optional[Literal["created_at", "updated_at", "title"]] = Field(
        default=None,
        description="Field to sort by"
    )
    sort_order: Optional[Literal["asc", "desc"]] = Field(
        default=None,
        description="Sort order (ascending or descending)"
    )


class TaskItem(BaseModel):
    """Task item in list response"""
    task_id: str
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime
    updated_at: datetime


class ListTasksResponse(BaseModel):
    """Response model for list_tasks tool"""
    tasks: List[TaskItem]
    count: int
    filter_applied: str


def list_tasks(
    request: ListTasksRequest,
    token_user_id: str,
    session: Session
) -> ListTasksResponse:
    """
    Retrieve all tasks for the authenticated user with optional filtering.

    Args:
        request: ListTasksRequest with user_id, filter, sort options
        token_user_id: User ID extracted from JWT token
        session: Database session

    Returns:
        ListTasksResponse with tasks, count, and filter_applied

    Raises:
        ValidationError: If input validation fails
        AuthorizationError: If user_id doesn't match token
        DatabaseError: If database operation fails
    """
    # Validate inputs
    validate_user_id(request.user_id)

    # Verify authorization
    verify_user_authorization(request.user_id, token_user_id)

    try:
        # Build base query
        statement = select(Task).where(Task.user_id == request.user_id)

        # Apply completion filter
        if request.filter == "pending":
            statement = statement.where(Task.completed == False)
        elif request.filter == "completed":
            statement = statement.where(Task.completed == True)
        # "all" filter doesn't add a WHERE clause

        # Apply sorting
        if request.sort_by:
            sort_column = getattr(Task, request.sort_by)
            if request.sort_order == "desc":
                statement = statement.order_by(col(sort_column).desc())
            else:
                statement = statement.order_by(col(sort_column).asc())
        else:
            # Default sort: created_at descending (newest first)
            statement = statement.order_by(col(Task.created_at).desc())

        # Execute query
        tasks = session.exec(statement).all()

        # Convert to response format
        task_items = [
            TaskItem(
                task_id=str(task.id),
                title=task.title,
                description=task.description,
                completed=task.completed,
                created_at=task.created_at,
                updated_at=task.updated_at
            )
            for task in tasks
        ]

        return ListTasksResponse(
            tasks=task_items,
            count=len(task_items),
            filter_applied=request.filter
        )

    except Exception as e:
        raise DatabaseError(
            message="Failed to retrieve tasks",
            details={"error": str(e)}
        )
