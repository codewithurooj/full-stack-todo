"""Validation utilities for task data"""
import re
from typing import List, Optional
from fastapi import HTTPException, status


def validate_priority(priority: str) -> None:
    """
    Validate priority value.

    Args:
        priority: Priority value to validate

    Raises:
        HTTPException: If priority is invalid
    """
    valid_priorities = ["high", "medium", "low"]
    if priority not in valid_priorities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid priority. Must be one of: {', '.join(valid_priorities)}"
        )


def validate_tag_name(tag: str) -> None:
    """
    Validate individual tag format.

    Rules:
    - Max 50 characters
    - Alphanumeric, hyphens, and underscores only
    - Cannot be empty

    Args:
        tag: Tag name to validate

    Raises:
        HTTPException: If tag format is invalid
    """
    if not tag or len(tag.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag cannot be empty"
        )

    if len(tag) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag '{tag}' exceeds maximum length of 50 characters"
        )

    # Allow alphanumeric, hyphens, underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, tag):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag '{tag}' contains invalid characters. Only alphanumeric, hyphens, and underscores allowed"
        )


def validate_tags(tags: List[str]) -> None:
    """
    Validate tags array.

    Rules:
    - Maximum 50 tags
    - Each tag must pass validate_tag_name()

    Args:
        tags: List of tags to validate

    Raises:
        HTTPException: If tags array is invalid
    """
    if len(tags) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum 50 tags allowed. Received {len(tags)} tags"
        )

    # Validate each tag
    for tag in tags:
        validate_tag_name(tag)


def validate_date_range(date_from: Optional[str], date_to: Optional[str]) -> None:
    """
    Validate date range filters.

    Rules:
    - If provided, dates must be valid ISO 8601 format
    - date_from must be before or equal to date_to

    Args:
        date_from: Start date in ISO 8601 format
        date_to: End date in ISO 8601 format

    Raises:
        HTTPException: If date range is invalid
    """
    from datetime import datetime

    # Validate date_from format
    if date_from:
        try:
            parsed_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date_from format: '{date_from}'. Must be ISO 8601 format (e.g., '2024-01-15T00:00:00Z')"
            )

    # Validate date_to format
    if date_to:
        try:
            parsed_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date_to format: '{date_to}'. Must be ISO 8601 format (e.g., '2024-01-15T23:59:59Z')"
            )

    # Validate date range
    if date_from and date_to:
        try:
            parsed_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            parsed_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))

            if parsed_from > parsed_to:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date range: date_from ({date_from}) must be before or equal to date_to ({date_to})"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error validating date range: {str(e)}"
            )
