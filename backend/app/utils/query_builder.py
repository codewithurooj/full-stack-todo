"""Query builder utility for task filtering and sorting"""
from sqlmodel import select
from sqlalchemy import case
from typing import Optional, List
from datetime import datetime, timedelta
import pytz
from app.models.task import Task
from app.utils.timezone import convert_to_utc, get_current_utc


def build_tasks_query(
    user_id: str,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    due_date_from: Optional[str] = None,
    due_date_to: Optional[str] = None,
    relative_range: Optional[str] = None,
    user_timezone: str = "UTC"
):
    """
    Build filtered and sorted tasks query.

    Args:
        user_id: User ID to filter tasks
        priority: Filter by priority (high|medium|low)
        tags: Filter by tags (array of tag names)
        status: Filter by status (all|pending|completed)
        search: Search keyword for title/description
        sort_by: Sort field (priority|due_date|created_at|title)
        sort_order: Sort order (asc|desc)
        date_from: Filter tasks created from this date (ISO 8601)
        date_to: Filter tasks created until this date (ISO 8601)
        due_date_from: Filter tasks due from this date (ISO 8601)
        due_date_to: Filter tasks due until this date (ISO 8601)
        relative_range: Filter by relative date range (today|this_week|this_month|overdue)
        user_timezone: User's IANA timezone for relative date calculations (default: UTC)

    Returns:
        SQLModel query object with filters and sorting applied
    """
    # Start with base query
    query = select(Task).where(Task.user_id == user_id)

    # Apply priority filter
    if priority:
        query = query.where(Task.priority == priority)

    # Apply tags filter (PostgreSQL overlap operator)
    if tags and len(tags) > 0:
        query = query.where(Task.tags.overlap(tags))

    # Apply status filter
    if status == "completed":
        query = query.where(Task.completed == True)
    elif status == "pending":
        query = query.where(Task.completed == False)
    # If status == "all" or None, no filter applied

    # Apply search filter (ILIKE for case-insensitive)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Task.title.ilike(search_pattern)) |
            (Task.description.ilike(search_pattern))
        )

    # Apply date range filters
    if date_from:
        query = query.where(Task.created_at >= date_from)
    if date_to:
        query = query.where(Task.created_at <= date_to)

    # Apply due date range filters
    if due_date_from or due_date_to:
        # Convert to UTC for comparison
        try:
            if due_date_from:
                from_dt = datetime.fromisoformat(due_date_from.replace('Z', '+00:00'))
                if from_dt.tzinfo is None:
                    # Assume user's timezone and convert to UTC
                    from_dt = convert_to_utc(from_dt, user_timezone)
                query = query.where(Task.due_date >= from_dt)

            if due_date_to:
                to_dt = datetime.fromisoformat(due_date_to.replace('Z', '+00:00'))
                if to_dt.tzinfo is None:
                    # Assume user's timezone and convert to UTC
                    to_dt = convert_to_utc(to_dt, user_timezone)
                query = query.where(Task.due_date <= to_dt)
        except (ValueError, TypeError):
            # Invalid date format, skip filter
            pass

    # Apply relative date range filter
    if relative_range:
        try:
            user_tz = pytz.timezone(user_timezone)
            now = get_current_utc()
            user_now = now.astimezone(user_tz)

            if relative_range == "today":
                # Midnight to 11:59:59 PM today in user's timezone
                start_of_day = user_now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = user_now.replace(hour=23, minute=59, second=59, microsecond=999999)
                start_utc = start_of_day.astimezone(pytz.UTC)
                end_utc = end_of_day.astimezone(pytz.UTC)
                query = query.where(Task.due_date >= start_utc)
                query = query.where(Task.due_date <= end_utc)

            elif relative_range == "this_week":
                # Start of week (Monday) to end of week (Sunday)
                start_of_week = user_now - timedelta(days=user_now.weekday())
                start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
                start_utc = start_of_week.astimezone(pytz.UTC)
                end_utc = end_of_week.astimezone(pytz.UTC)
                query = query.where(Task.due_date >= start_utc)
                query = query.where(Task.due_date <= end_utc)

            elif relative_range == "this_month":
                # First day to last day of month
                start_of_month = user_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                # Get last day of month
                if user_now.month == 12:
                    end_of_month = user_now.replace(year=user_now.year + 1, month=1, day=1)
                else:
                    end_of_month = user_now.replace(month=user_now.month + 1, day=1)
                end_of_month = end_of_month - timedelta(microseconds=1)
                start_utc = start_of_month.astimezone(pytz.UTC)
                end_utc = end_of_month.astimezone(pytz.UTC)
                query = query.where(Task.due_date >= start_utc)
                query = query.where(Task.due_date <= end_utc)

            elif relative_range == "overdue":
                # due_date < now AND not completed
                query = query.where(Task.due_date < now)
                query = query.where(Task.completed == False)

        except pytz.UnknownTimeZoneError:
            # Invalid timezone, skip filter
            pass

    # Apply sorting
    if sort_by == "priority":
        # Custom order: high (1) > medium (2) > low (3)
        priority_order = case(
            (Task.priority == 'high', 1),
            (Task.priority == 'medium', 2),
            (Task.priority == 'low', 3),
            else_=4
        )
        if sort_order == "asc":
            query = query.order_by(priority_order.asc())
        else:
            query = query.order_by(priority_order.desc())
    elif sort_by == "due_date":
        # NULL due dates should appear last regardless of sort order
        if sort_order == "asc":
            # Earliest first, NULL last
            query = query.order_by(Task.due_date.asc().nullslast())
        else:
            # Latest first, NULL last
            query = query.order_by(Task.due_date.desc().nullslast())
    elif sort_by == "title":
        if sort_order == "asc":
            query = query.order_by(Task.title.asc())
        else:
            query = query.order_by(Task.title.desc())
    elif sort_by == "created_at":
        if sort_order == "asc":
            query = query.order_by(Task.created_at.asc())
        else:
            query = query.order_by(Task.created_at.desc())

    return query
