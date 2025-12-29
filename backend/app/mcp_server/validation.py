"""Shared validation utilities for MCP tools"""
import re
from typing import Optional
from app.mcp_server.errors import ValidationError

# UUID v4 regex pattern
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.IGNORECASE)


def validate_user_id(user_id: str) -> None:
    """
    Validate user_id format.

    Args:
        user_id: User identifier string

    Raises:
        ValidationError: If user_id is empty or invalid
    """
    if not user_id or not user_id.strip():
        raise ValidationError(
            message="user_id is required",
            details={"field": "user_id", "value": user_id}
        )


def validate_task_id(task_id: str) -> None:
    """
    Validate task_id is a valid UUID.

    Args:
        task_id: Task identifier string

    Raises:
        ValidationError: If task_id is not a valid UUID format
    """
    if not task_id or not task_id.strip():
        raise ValidationError(
            message="task_id is required",
            details={"field": "task_id", "value": task_id}
        )

    if not UUID_PATTERN.match(task_id):
        raise ValidationError(
            message="task_id must be a valid UUID",
            details={"field": "task_id", "value": task_id}
        )


def validate_title(title: Optional[str], required: bool = True) -> None:
    """
    Validate task title.

    Args:
        title: Task title string
        required: Whether title is required

    Raises:
        ValidationError: If title validation fails
    """
    if required and (not title or not title.strip()):
        raise ValidationError(
            message="title is required and cannot be empty",
            details={"field": "title"}
        )

    if title and len(title) > 200:
        raise ValidationError(
            message="title exceeds maximum length of 200 characters",
            details={"field": "title", "max_length": 200, "actual_length": len(title)}
        )


def validate_description(description: Optional[str]) -> None:
    """
    Validate task description (optional field).

    Args:
        description: Task description string

    Raises:
        ValidationError: If description exceeds max length
    """
    if description and len(description) > 1000:
        raise ValidationError(
            message="description exceeds maximum length of 1000 characters",
            details={"field": "description", "max_length": 1000, "actual_length": len(description)}
        )
