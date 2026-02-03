"""Timezone conversion utilities for handling user timezones and UTC storage.

This module provides functions for converting between UTC and user timezones,
handling DST transitions properly using pytz.
"""

from datetime import datetime
from typing import Optional
import pytz
from pytz.exceptions import UnknownTimeZoneError


def convert_to_utc(local_dt: datetime, timezone_str: str) -> datetime:
    """Convert a local datetime to UTC.

    Args:
        local_dt: Naive or aware datetime in the local timezone
        timezone_str: IANA timezone name (e.g., 'America/New_York', 'UTC')

    Returns:
        Timezone-aware datetime in UTC

    Raises:
        ValueError: If timezone_str is invalid or datetime conversion fails
        UnknownTimeZoneError: If timezone_str is not a valid IANA timezone

    Example:
        >>> from datetime import datetime
        >>> local_dt = datetime(2026, 2, 15, 9, 0)  # 9 AM EST
        >>> utc_dt = convert_to_utc(local_dt, 'America/New_York')
        >>> utc_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
        '2026-02-15 14:00:00 UTC'
    """
    try:
        # Get the timezone object
        user_tz = pytz.timezone(timezone_str)

        # If datetime is naive, localize it to the user timezone
        if local_dt.tzinfo is None:
            # Use localize to handle DST transitions properly
            local_dt_aware = user_tz.localize(local_dt)
        else:
            # If already aware, convert to the user timezone first
            local_dt_aware = local_dt.astimezone(user_tz)

        # Convert to UTC
        utc_dt = local_dt_aware.astimezone(pytz.UTC)

        return utc_dt

    except UnknownTimeZoneError as e:
        raise ValueError(f"Invalid timezone: {timezone_str}") from e
    except Exception as e:
        raise ValueError(f"Failed to convert datetime to UTC: {str(e)}") from e


def convert_from_utc(utc_dt: datetime, timezone_str: str) -> datetime:
    """Convert a UTC datetime to a user's local timezone.

    Args:
        utc_dt: Timezone-aware datetime in UTC
        timezone_str: IANA timezone name (e.g., 'America/New_York', 'UTC')

    Returns:
        Timezone-aware datetime in the user's timezone

    Raises:
        ValueError: If timezone_str is invalid or datetime is not UTC-aware
        UnknownTimeZoneError: If timezone_str is not a valid IANA timezone

    Example:
        >>> from datetime import datetime
        >>> import pytz
        >>> utc_dt = datetime(2026, 2, 15, 14, 0, tzinfo=pytz.UTC)
        >>> local_dt = convert_from_utc(utc_dt, 'America/New_York')
        >>> local_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
        '2026-02-15 09:00:00 EST'
    """
    try:
        # Validate that utc_dt is timezone-aware
        if utc_dt.tzinfo is None:
            raise ValueError("utc_dt must be timezone-aware")

        # Get the user timezone object
        user_tz = pytz.timezone(timezone_str)

        # Convert UTC to user timezone
        local_dt = utc_dt.astimezone(user_tz)

        return local_dt

    except UnknownTimeZoneError as e:
        raise ValueError(f"Invalid timezone: {timezone_str}") from e
    except Exception as e:
        raise ValueError(f"Failed to convert datetime from UTC: {str(e)}") from e


def get_user_timezone(timezone_str: Optional[str] = None) -> str:
    """Get and validate user timezone, falling back to UTC if not provided.

    Args:
        timezone_str: Optional IANA timezone name

    Returns:
        Valid IANA timezone string (defaults to 'UTC' if None or invalid)

    Example:
        >>> get_user_timezone('America/New_York')
        'America/New_York'
        >>> get_user_timezone(None)
        'UTC'
        >>> get_user_timezone('Invalid/Timezone')
        'UTC'
    """
    # Default to UTC if no timezone provided
    if timezone_str is None or timezone_str == "":
        return "UTC"

    # Validate the timezone
    try:
        pytz.timezone(timezone_str)
        return timezone_str
    except UnknownTimeZoneError:
        # Invalid timezone, fall back to UTC
        return "UTC"


def is_valid_timezone(timezone_str: str) -> bool:
    """Check if a timezone string is valid.

    Args:
        timezone_str: IANA timezone name to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> is_valid_timezone('America/New_York')
        True
        >>> is_valid_timezone('Invalid/Timezone')
        False
    """
    try:
        pytz.timezone(timezone_str)
        return True
    except UnknownTimeZoneError:
        return False


def get_current_utc() -> datetime:
    """Get the current UTC time as a timezone-aware datetime.

    Returns:
        Current datetime in UTC with timezone info

    Example:
        >>> now = get_current_utc()
        >>> now.tzinfo == pytz.UTC
        True
    """
    return datetime.now(pytz.UTC)
