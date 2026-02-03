"""Add Task tool for MCP server"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.models.task import Task
from app.mcp_server.errors import DatabaseError, ValidationError
from app.mcp_server.validation import validate_user_id, validate_title, validate_description
from app.mcp_server.auth import verify_user_authorization
from app.mcp_server.nlp_utils import normalize_priority, normalize_tags
from app.utils.date_parser import parse_flexible_date
from app.utils.timezone import convert_to_utc


class AddTaskRequest(BaseModel):
    """Request model for add_task tool"""
    user_id: str = Field(..., description="User identifier (must match JWT token)")
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Optional task description")
    priority: Optional[str] = Field("medium", description="Task priority: high, medium, or low (default: medium)")
    tags: Optional[List[str]] = Field(default_factory=list, description="Task tags (optional list of strings)")
    due_date: Optional[str] = Field(None, description="Task due date (flexible format: 'tomorrow 9am', '2026-02-15 14:30', 'next friday')")
    timezone: Optional[str] = Field("UTC", description="User timezone for due date conversion (default: UTC)")


class AddTaskResponse(BaseModel):
    """Response model for add_task tool"""
    task_id: str
    title: str
    description: Optional[str]
    completed: bool
    priority: str
    tags: List[str]
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime


def add_task(
    request: AddTaskRequest,
    token_user_id: str,
    session: Session
) -> AddTaskResponse:
    """
    Create a new task for the authenticated user with NLP-enhanced priority and tags.

    Args:
        request: AddTaskRequest with user_id, title, description, priority, tags
        token_user_id: User ID extracted from JWT token
        session: Database session

    Returns:
        AddTaskResponse with created task details

    Raises:
        ValidationError: If input validation fails
        AuthorizationError: If user_id doesn't match token
        DatabaseError: If database operation fails

    NLP Features:
        - Extracts priority from title/description if not explicitly provided
        - Extracts tags from title/description using multiple patterns
        - Priority keywords: urgent/critical → high, normal → medium, someday → low
        - Tag patterns: "with tags work", "#work", "tagged as work"
    """
    # Validate inputs
    validate_user_id(request.user_id)
    validate_title(request.title, required=True)
    validate_description(request.description)

    # Verify authorization
    verify_user_authorization(request.user_id, token_user_id)

    try:
        # Combine title and description for NLP extraction
        full_text = f"{request.title} {request.description or ''}"

        # Normalize priority with NLP fallback
        normalized_priority = normalize_priority(request.priority, full_text)

        # Normalize tags with NLP fallback
        normalized_tags = normalize_tags(request.tags, full_text)

        # Parse and convert due date if provided
        parsed_due_date = None
        if request.due_date:
            try:
                # Parse flexible date
                parsed_dt = parse_flexible_date(
                    request.due_date,
                    timezone_str=request.timezone or "UTC"
                )
                # Convert to UTC
                parsed_due_date = convert_to_utc(parsed_dt, request.timezone or "UTC")
            except (ValueError, Exception) as e:
                raise ValidationError(
                    message="Invalid due date format",
                    details={"due_date": request.due_date, "error": str(e)}
                )

        # Create task
        db_task = Task(
            user_id=request.user_id,
            title=request.title.strip(),
            description=request.description.strip() if request.description else None,
            completed=False,
            priority=normalized_priority,
            tags=normalized_tags,
            due_date=parsed_due_date,
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
            priority=db_task.priority,
            tags=db_task.tags,
            due_date=db_task.due_date,
            created_at=db_task.created_at,
            updated_at=db_task.updated_at
        )

    except Exception as e:
        session.rollback()
        raise DatabaseError(
            message="Failed to create task",
            details={"error": str(e)}
        )
