"""Flexible date parsing utilities for natural language and structured date inputs.

This module provides functions to parse various date formats including:
- ISO 8601: "2024-01-15T14:30:00"
- Natural language: "tomorrow 9am", "next friday 2pm"
- Relative dates: "today", "tomorrow", "next week"

All returned datetimes are timezone-aware.
"""

from datetime import datetime, timedelta
from typing import Optional, Union
from dateutil import parser
from dateutil.relativedelta import relativedelta
import pytz
import re


def parse_flexible_date(
    date_string: str,
    timezone_str: str = "UTC",
    base_date: Optional[datetime] = None
) -> datetime:
    """Parse flexible date inputs into timezone-aware datetime objects.

    Supports multiple formats:
    - ISO 8601: "2024-01-15T14:30:00", "2024-01-15 14:30"
    - Natural language: "tomorrow 9am", "next friday 2pm"
    - Relative: "today", "tomorrow", "next week", "in 3 days"

    Args:
        date_string: Date string to parse
        timezone_str: IANA timezone for interpreting the date (default: UTC)
        base_date: Reference date for relative parsing (default: current time)

    Returns:
        Timezone-aware datetime object in the specified timezone

    Raises:
        ValueError: If date_string cannot be parsed

    Examples:
        >>> parse_flexible_date("2024-01-15 14:30", "America/New_York")
        datetime(2024, 1, 15, 14, 30, tzinfo=<DstTzInfo 'America/New_York' EST-1 day, 19:00:00 STD>)

        >>> parse_flexible_date("tomorrow 9am", "UTC")
        datetime(2026, 1, 10, 9, 0, tzinfo=<UTC>)

        >>> parse_flexible_date("next friday 2pm", "America/Los_Angeles")
        datetime(2026, 1, 16, 14, 0, tzinfo=<DstTzInfo 'America/Los_Angeles' PST-1 day, 16:00:00 STD>)
    """
    if not date_string or not isinstance(date_string, str):
        raise ValueError("date_string must be a non-empty string")

    # Get timezone object
    try:
        user_tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        raise ValueError(f"Invalid timezone: {timezone_str}")

    # Use current time in user timezone if no base_date provided
    if base_date is None:
        base_date = datetime.now(user_tz)
    elif base_date.tzinfo is None:
        # Localize naive base_date to user timezone
        base_date = user_tz.localize(base_date)

    # Normalize input
    date_string_lower = date_string.lower().strip()

    # Try to parse relative dates first
    relative_dt = _parse_relative_date(date_string_lower, base_date, user_tz)
    if relative_dt:
        return relative_dt

    # Try standard dateutil parser
    try:
        # Use a clean base date for better parsing (zero out time)
        clean_base = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
        parsed_dt = parser.parse(date_string, default=clean_base, fuzzy=True)

        # If parsed datetime is naive, localize to user timezone
        if parsed_dt.tzinfo is None:
            parsed_dt = user_tz.localize(parsed_dt)

        return parsed_dt

    except (parser.ParserError, ValueError) as e:
        # If standard parsing fails, it might be a truly invalid string
        # Try one more time to see if it's just unparseable
        try:
            # Attempt basic validation
            if len(date_string.strip()) < 3 or not any(c.isdigit() or c.isalpha() for c in date_string):
                raise ValueError(f"Unable to parse date string '{date_string}': {str(e)}") from e
        except:
            pass
        raise ValueError(f"Unable to parse date string '{date_string}': {str(e)}") from e


def _parse_relative_date(
    date_string: str,
    base_date: datetime,
    user_tz: pytz.tzinfo
) -> Optional[datetime]:
    """Parse relative date expressions.

    Args:
        date_string: Lowercase date string
        base_date: Reference datetime
        user_tz: User's timezone

    Returns:
        Parsed datetime or None if not a relative expression
    """
    # Extract time component if present (e.g., "tomorrow 9am")
    time_match = re.search(r'(\d{1,2})\s*(am|pm|:)', date_string)
    target_hour = None
    target_minute = 0

    if time_match:
        # Parse time component
        time_str = date_string[time_match.start():]
        try:
            # Use a clean base with zero time for better parsing
            clean_base = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
            time_parsed = parser.parse(time_str, default=clean_base, fuzzy=True)
            target_hour = time_parsed.hour
            target_minute = time_parsed.minute
        except parser.ParserError:
            pass

    # Remove time component for date parsing
    date_only = re.sub(r'\d{1,2}\s*(am|pm|:\d{2})', '', date_string).strip()

    # Today
    if date_only in ['today', 'now']:
        result = base_date.replace(microsecond=0)
        if target_hour is not None:
            result = result.replace(hour=target_hour, minute=target_minute, second=0)
        return result

    # Tomorrow
    if date_only in ['tomorrow', 'tmr', 'tmrw']:
        result = base_date + timedelta(days=1)
        if target_hour is not None:
            result = result.replace(hour=target_hour, minute=target_minute, second=0)
        else:
            result = result.replace(hour=9, minute=0, second=0)  # Default to 9 AM
        return result

    # Yesterday
    if date_only in ['yesterday']:
        result = base_date - timedelta(days=1)
        if target_hour is not None:
            result = result.replace(hour=target_hour, minute=target_minute, second=0)
        return result

    # Next week
    if 'next week' in date_only:
        result = base_date + timedelta(weeks=1)
        if target_hour is not None:
            result = result.replace(hour=target_hour, minute=target_minute, second=0)
        else:
            result = result.replace(hour=9, minute=0, second=0)
        return result

    # Next month
    if 'next month' in date_only:
        result = base_date + relativedelta(months=1)
        if target_hour is not None:
            result = result.replace(hour=target_hour, minute=target_minute, second=0)
        return result

    # In X days/weeks/months
    in_match = re.match(r'in\s+(\d+)\s+(day|week|month|hour|minute)s?', date_only)
    if in_match:
        amount = int(in_match.group(1))
        unit = in_match.group(2)

        if unit == 'day':
            result = base_date + timedelta(days=amount)
        elif unit == 'week':
            result = base_date + timedelta(weeks=amount)
        elif unit == 'month':
            result = base_date + relativedelta(months=amount)
        elif unit == 'hour':
            result = base_date + timedelta(hours=amount)
        elif unit == 'minute':
            result = base_date + timedelta(minutes=amount)
        else:
            return None

        if target_hour is not None:
            result = result.replace(hour=target_hour, minute=target_minute, second=0)
        return result

    # Next [weekday]
    weekdays = {
        'monday': 0, 'mon': 0,
        'tuesday': 1, 'tue': 1, 'tues': 1,
        'wednesday': 2, 'wed': 2,
        'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
        'friday': 4, 'fri': 4,
        'saturday': 5, 'sat': 5,
        'sunday': 6, 'sun': 6
    }

    for day_name, day_num in weekdays.items():
        if f'next {day_name}' in date_only or date_only == day_name:
            # Calculate days until next occurrence
            current_weekday = base_date.weekday()
            days_ahead = (day_num - current_weekday) % 7
            if days_ahead == 0:
                days_ahead = 7  # Next week if same day

            result = base_date + timedelta(days=days_ahead)
            if target_hour is not None:
                result = result.replace(hour=target_hour, minute=target_minute, second=0)
            else:
                result = result.replace(hour=9, minute=0, second=0)
            return result

    return None


def parse_time_string(time_string: str, base_date: Optional[datetime] = None) -> datetime:
    """Parse a time string and combine with base date.

    Args:
        time_string: Time string like "9am", "14:30", "2:30pm"
        base_date: Date to combine with (default: today)

    Returns:
        Datetime with parsed time

    Raises:
        ValueError: If time_string cannot be parsed

    Example:
        >>> parse_time_string("9am")
        datetime(2026, 1, 9, 9, 0)
    """
    if base_date is None:
        base_date = datetime.now()

    try:
        # Use a fixed base date with zero minutes/seconds for time parsing
        zero_base = datetime(base_date.year, base_date.month, base_date.day, 0, 0, 0)
        parsed = parser.parse(time_string, default=zero_base, fuzzy=True)
        return base_date.replace(
            hour=parsed.hour,
            minute=parsed.minute,
            second=0,
            microsecond=0
        )
    except parser.ParserError as e:
        raise ValueError(f"Unable to parse time string '{time_string}': {str(e)}") from e


def is_past_due(due_date: datetime, reference_time: Optional[datetime] = None) -> bool:
    """Check if a due date is in the past.

    Args:
        due_date: Due date to check
        reference_time: Time to compare against (default: current UTC time)

    Returns:
        True if due_date is in the past

    Example:
        >>> from datetime import datetime
        >>> import pytz
        >>> past = datetime(2020, 1, 1, tzinfo=pytz.UTC)
        >>> is_past_due(past)
        True
    """
    if reference_time is None:
        reference_time = datetime.now(pytz.UTC)

    # Ensure both datetimes are timezone-aware for comparison
    if due_date.tzinfo is None:
        due_date = pytz.UTC.localize(due_date)
    if reference_time.tzinfo is None:
        reference_time = pytz.UTC.localize(reference_time)

    return due_date < reference_time


def format_relative_time(due_date: datetime, reference_time: Optional[datetime] = None) -> str:
    """Format a due date as relative time (e.g., 'in 2 hours', '3 days ago').

    Args:
        due_date: Due date to format
        reference_time: Time to compare against (default: current UTC time)

    Returns:
        Human-readable relative time string

    Example:
        >>> from datetime import datetime, timedelta
        >>> import pytz
        >>> tomorrow = datetime.now(pytz.UTC) + timedelta(days=1)
        >>> format_relative_time(tomorrow)
        'in 1 day'
    """
    if reference_time is None:
        reference_time = datetime.now(pytz.UTC)

    # Ensure both datetimes are timezone-aware
    if due_date.tzinfo is None:
        due_date = pytz.UTC.localize(due_date)
    if reference_time.tzinfo is None:
        reference_time = pytz.UTC.localize(reference_time)

    delta = due_date - reference_time
    total_seconds = delta.total_seconds()

    if total_seconds < 0:
        # Past
        total_seconds = abs(total_seconds)
        suffix = "ago"
    else:
        # Future
        suffix = "in"

    # Calculate units
    minutes = int(total_seconds / 60)
    hours = int(total_seconds / 3600)
    days = int(total_seconds / 86400)
    weeks = int(total_seconds / 604800)
    months = int(total_seconds / 2592000)  # Approximate

    if total_seconds < 60:
        return "just now" if suffix == "ago" else "in a moment"
    elif minutes < 60:
        unit = "minute" if minutes == 1 else "minutes"
        return f"{suffix} {minutes} {unit}" if suffix == "in" else f"{minutes} {unit} {suffix}"
    elif hours < 24:
        unit = "hour" if hours == 1 else "hours"
        return f"{suffix} {hours} {unit}" if suffix == "in" else f"{hours} {unit} {suffix}"
    elif days < 7:
        unit = "day" if days == 1 else "days"
        return f"{suffix} {days} {unit}" if suffix == "in" else f"{days} {unit} {suffix}"
    elif weeks < 4:
        unit = "week" if weeks == 1 else "weeks"
        return f"{suffix} {weeks} {unit}" if suffix == "in" else f"{weeks} {unit} {suffix}"
    else:
        unit = "month" if months == 1 else "months"
        return f"{suffix} {months} {unit}" if suffix == "in" else f"{months} {unit} {suffix}"
