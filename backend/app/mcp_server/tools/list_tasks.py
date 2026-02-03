"""List Tasks tool for MCP server"""
from typing import Optional, Literal, List
from datetime import datetime
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.models.task import Task
from app.mcp_server.errors import DatabaseError
from app.mcp_server.validation import validate_user_id
from app.mcp_server.auth import verify_user_authorization
from app.mcp_server.nlp_utils import parse_filter_intent, extract_sort_intent
from app.utils.query_builder import build_tasks_query


class ListTasksRequest(BaseModel):
    """Request model for list_tasks tool"""
    user_id: str = Field(..., description="User identifier (must match JWT token)")
    filter: Optional[Literal["all", "pending", "completed"]] = Field(
        default="all",
        description="Filter tasks by completion status"
    )
    priority: Optional[Literal["high", "medium", "low"]] = Field(
        default=None,
        description="Filter tasks by priority level"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Filter tasks by tags (returns tasks with any of the specified tags)"
    )
    search: Optional[str] = Field(
        default=None,
        description="Search keyword for title/description (case-insensitive)"
    )
    sort_by: Optional[Literal["created_at", "title", "priority"]] = Field(
        default=None,
        description="Field to sort by"
    )
    sort_order: Optional[Literal["asc", "desc"]] = Field(
        default=None,
        description="Sort order (ascending or descending)"
    )
    query: Optional[str] = Field(
        default=None,
        description="Natural language query for filtering (e.g., 'show high priority work tasks')"
    )


class TaskItem(BaseModel):
    """Task item in list response"""
    task_id: str
    title: str
    description: Optional[str]
    completed: bool
    priority: str
    tags: List[str]
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class ListTasksResponse(BaseModel):
    """Response model for list_tasks tool"""
    tasks: List[TaskItem]
    count: int
    filters_applied: dict


def list_tasks(
    request: ListTasksRequest,
    token_user_id: str,
    session: Session
) -> ListTasksResponse:
    """
    Retrieve tasks with advanced filtering and NLP query support.

    Args:
        request: ListTasksRequest with user_id, filters, search, sort options, and optional NLP query
        token_user_id: User ID extracted from JWT token
        session: Database session

    Returns:
        ListTasksResponse with tasks, count, and filters_applied

    Raises:
        ValidationError: If input validation fails
        AuthorizationError: If user_id doesn't match token
        DatabaseError: If database operation fails

    NLP Features:
        - Natural language queries: "show high priority work tasks"
        - Priority detection: "high priority" → priority="high"
        - Tag detection: "my work tasks" → tags=["work"]
        - Search detection: "find tasks about meeting" → search="meeting"
        - Sort detection: "sort by priority", "newest first"
    """
    # Validate inputs
    validate_user_id(request.user_id)

    # Verify authorization
    verify_user_authorization(request.user_id, token_user_id)

    try:
        # Initialize filter parameters
        priority_filter = request.priority
        tags_filter = request.tags if request.tags else []
        search_filter = request.search
        sort_by = request.sort_by or "created_at"
        sort_order = request.sort_order or "desc"
        status_filter = request.filter

        # Parse natural language query if provided
        if request.query:
            nlp_filters = parse_filter_intent(request.query)

            # Apply NLP filters if explicit filters not provided
            if not priority_filter and nlp_filters.get("priority"):
                priority_filter = nlp_filters["priority"]

            if not tags_filter and nlp_filters.get("tags"):
                tags_filter = nlp_filters["tags"]

            if not search_filter and nlp_filters.get("search"):
                search_filter = nlp_filters["search"]

            # Extract sort preferences from NLP query
            nlp_sort_by, nlp_sort_order = extract_sort_intent(request.query)
            if not request.sort_by and nlp_sort_by:
                sort_by = nlp_sort_by
            if not request.sort_order and nlp_sort_order:
                sort_order = nlp_sort_order

        # Build query using query builder utility
        statement = build_tasks_query(
            user_id=request.user_id,
            priority=priority_filter,
            tags=tags_filter if tags_filter else None,
            status=status_filter,
            search=search_filter,
            sort_by=sort_by,
            sort_order=sort_order
        )

        # Execute query
        tasks = session.exec(statement).all()

        # Convert to response format
        task_items = [
            TaskItem(
                task_id=str(task.id),
                title=task.title,
                description=task.description,
                completed=task.completed,
                priority=task.priority,
                tags=task.tags,
                due_date=task.due_date,
                created_at=task.created_at,
                updated_at=task.updated_at
            )
            for task in tasks
        ]

        # Build filters summary
        filters_applied = {
            "status": status_filter,
            "priority": priority_filter,
            "tags": tags_filter,
            "search": search_filter,
            "sort_by": sort_by,
            "sort_order": sort_order
        }

        return ListTasksResponse(
            tasks=task_items,
            count=len(task_items),
            filters_applied=filters_applied
        )

    except Exception as e:
        raise DatabaseError(
            message="Failed to retrieve tasks",
            details={"error": str(e)}
        )
