"""Recurrence pattern generation utilities using dateutil.rrule.

This module provides a wrapper around dateutil.rrule for generating
recurring task instances based on RFC 5545 RRULE patterns.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dateutil import rrule
import pytz


def generate_next_occurrence(
    pattern: str,
    interval: int = 1,
    days: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    count: int = 1,
    timezone_str: str = "UTC"
) -> Optional[datetime]:
    """Generate the next occurrence of a recurring pattern.

    Args:
        pattern: Recurrence frequency ('daily', 'weekly', 'monthly', 'custom')
        interval: Interval between occurrences (e.g., 2 for every 2 days)
        days: List of weekday names for weekly patterns (e.g., ['Monday', 'Friday'])
        start_date: Start date for recurrence (default: current time)
        end_date: End date for recurrence (optional)
        count: Number of occurrences to generate (default: 1 for next occurrence)
        timezone_str: IANA timezone name

    Returns:
        Next occurrence datetime, or None if no more occurrences

    Raises:
        ValueError: If pattern is invalid or parameters are incompatible

    Examples:
        >>> # Daily at 9 AM
        >>> generate_next_occurrence('daily', interval=1, start_date=datetime(2026, 1, 9, 9, 0))
        datetime(2026, 1, 10, 9, 0, tzinfo=<UTC>)

        >>> # Weekly on Monday and Friday
        >>> generate_next_occurrence('weekly', days=['Monday', 'Friday'], start_date=datetime(2026, 1, 9, 9, 0))
        datetime(2026, 1, 10, 9, 0, tzinfo=<UTC>)
    """
    # Get timezone
    try:
        tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        raise ValueError(f"Invalid timezone: {timezone_str}")

    # Default start_date to current time
    if start_date is None:
        start_date = datetime.now(tz)
    elif start_date.tzinfo is None:
        start_date = tz.localize(start_date)

    # Generate occurrences - get count+1 to skip the start_date itself
    occurrences = generate_occurrences(
        pattern=pattern,
        interval=interval,
        days=days,
        start_date=start_date,
        end_date=end_date,
        max_count=count + 1,  # Get one extra to skip start_date
        timezone_str=timezone_str
    )

    # Return the second occurrence (skip start_date, get next one)
    return occurrences[1] if len(occurrences) > 1 else None


def generate_occurrences(
    pattern: str,
    interval: int = 1,
    days: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    max_count: int = 10,
    timezone_str: str = "UTC"
) -> List[datetime]:
    """Generate multiple occurrences of a recurring pattern.

    Args:
        pattern: Recurrence frequency ('daily', 'weekly', 'monthly', 'custom')
        interval: Interval between occurrences
        days: List of weekday names for weekly patterns
        start_date: Start date for recurrence
        end_date: End date for recurrence (optional)
        max_count: Maximum number of occurrences to generate
        timezone_str: IANA timezone name

    Returns:
        List of datetime objects representing occurrences

    Raises:
        ValueError: If pattern is invalid or parameters are incompatible

    Examples:
        >>> # Next 5 daily occurrences
        >>> generate_occurrences('daily', max_count=5)
        [datetime(2026, 1, 10, 9, 0), datetime(2026, 1, 11, 9, 0), ...]
    """
    # Get timezone
    try:
        tz = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        raise ValueError(f"Invalid timezone: {timezone_str}")

    # Default start_date to current time
    if start_date is None:
        start_date = datetime.now(tz)
    elif start_date.tzinfo is None:
        start_date = tz.localize(start_date)

    # Validate and convert pattern to rrule frequency
    freq = _pattern_to_freq(pattern)

    # Build rrule parameters
    rrule_params: Dict[str, Any] = {
        'freq': freq,
        'dtstart': start_date,
        'interval': interval,
    }

    # Add end date if provided
    if end_date is not None:
        if end_date.tzinfo is None:
            end_date = tz.localize(end_date)
        rrule_params['until'] = end_date

    # Add count (limit to 365 for safety)
    rrule_params['count'] = min(max_count, 365)

    # Handle weekly pattern with specific days
    if pattern.lower() == 'weekly' and days:
        byweekday = _parse_weekdays(days)
        if byweekday:
            rrule_params['byweekday'] = byweekday

    try:
        # Generate rule
        rule = rrule.rrule(**rrule_params)

        # Get occurrences
        occurrences = list(rule)

        # Ensure all occurrences are timezone-aware
        return [
            occ if occ.tzinfo else tz.localize(occ)
            for occ in occurrences
        ]

    except Exception as e:
        raise ValueError(f"Failed to generate recurrence pattern: {str(e)}") from e


def _pattern_to_freq(pattern: str) -> int:
    """Convert pattern string to rrule frequency constant.

    Args:
        pattern: Pattern name ('daily', 'weekly', 'monthly', 'custom')

    Returns:
        rrule frequency constant

    Raises:
        ValueError: If pattern is not recognized
    """
    pattern_lower = pattern.lower()

    pattern_map = {
        'daily': rrule.DAILY,
        'weekly': rrule.WEEKLY,
        'monthly': rrule.MONTHLY,
        'yearly': rrule.YEARLY,
        'custom': rrule.DAILY,  # Default to daily for custom
    }

    if pattern_lower not in pattern_map:
        raise ValueError(f"Invalid pattern: {pattern}. Must be one of: daily, weekly, monthly, yearly, custom")

    return pattern_map[pattern_lower]


def _parse_weekdays(days: List[str]) -> List[int]:
    """Parse weekday names to rrule weekday constants.

    Args:
        days: List of weekday names (e.g., ['Monday', 'Friday'])

    Returns:
        List of rrule weekday constants

    Raises:
        ValueError: If any day name is invalid
    """
    weekday_map = {
        'monday': rrule.MO,
        'tuesday': rrule.TU,
        'wednesday': rrule.WE,
        'thursday': rrule.TH,
        'friday': rrule.FR,
        'saturday': rrule.SA,
        'sunday': rrule.SU,
        'mon': rrule.MO,
        'tue': rrule.TU,
        'wed': rrule.WE,
        'thu': rrule.TH,
        'fri': rrule.FR,
        'sat': rrule.SA,
        'sun': rrule.SU,
    }

    result = []
    for day in days:
        day_lower = day.lower().strip()
        if day_lower not in weekday_map:
            raise ValueError(f"Invalid weekday name: {day}")
        result.append(weekday_map[day_lower])

    return result


def parse_rrule_string(rrule_string: str, start_date: datetime) -> List[datetime]:
    """Parse an RFC 5545 RRULE string and generate occurrences.

    Args:
        rrule_string: RFC 5545 RRULE string (e.g., 'FREQ=DAILY;INTERVAL=1')
        start_date: Start date for the recurrence

    Returns:
        List of datetime objects (up to 100 occurrences)

    Raises:
        ValueError: If RRULE string is malformed

    Example:
        >>> rrule_str = 'FREQ=DAILY;INTERVAL=2;COUNT=5'
        >>> start = datetime(2026, 1, 9, 9, 0, tzinfo=pytz.UTC)
        >>> parse_rrule_string(rrule_str, start)
        [datetime(2026, 1, 9, 9, 0), datetime(2026, 1, 11, 9, 0), ...]
    """
    try:
        # Parse RRULE string
        rule = rrule.rrulestr(rrule_string, dtstart=start_date)

        # Generate up to 100 occurrences for safety
        occurrences = list(rule[:100])

        return occurrences

    except Exception as e:
        raise ValueError(f"Failed to parse RRULE string: {str(e)}") from e


def build_rrule_string(
    pattern: str,
    interval: int = 1,
    days: Optional[List[str]] = None,
    end_date: Optional[datetime] = None,
    count: Optional[int] = None
) -> str:
    """Build an RFC 5545 RRULE string from pattern parameters.

    Args:
        pattern: Recurrence frequency ('daily', 'weekly', 'monthly')
        interval: Interval between occurrences
        days: List of weekday names for weekly patterns
        end_date: End date for recurrence
        count: Number of occurrences

    Returns:
        RFC 5545 RRULE string

    Example:
        >>> build_rrule_string('daily', interval=1, count=30)
        'FREQ=DAILY;INTERVAL=1;COUNT=30'
        >>> build_rrule_string('weekly', days=['Monday', 'Friday'])
        'FREQ=WEEKLY;INTERVAL=1;BYDAY=MO,FR'
    """
    freq = _pattern_to_freq(pattern)

    # Map frequency constant to string
    freq_map = {
        rrule.DAILY: 'DAILY',
        rrule.WEEKLY: 'WEEKLY',
        rrule.MONTHLY: 'MONTHLY',
        rrule.YEARLY: 'YEARLY',
    }

    parts = [f"FREQ={freq_map.get(freq, 'DAILY')}"]

    # Only include interval if it's greater than 1 (1 is the default)
    if interval > 1:
        parts.append(f"INTERVAL={interval}")

    if pattern.lower() == 'weekly' and days:
        # Convert day names to BYDAY format
        day_abbrev_map = {
            'monday': 'MO', 'mon': 'MO',
            'tuesday': 'TU', 'tue': 'TU',
            'wednesday': 'WE', 'wed': 'WE',
            'thursday': 'TH', 'thu': 'TH',
            'friday': 'FR', 'fri': 'FR',
            'saturday': 'SA', 'sat': 'SA',
            'sunday': 'SU', 'sun': 'SU',
        }
        byday = ','.join([day_abbrev_map.get(d.lower(), '') for d in days if d.lower() in day_abbrev_map])
        if byday:
            parts.append(f"BYDAY={byday}")

    if end_date:
        # Format: UNTIL=20260515T143000Z
        until_str = end_date.strftime('%Y%m%dT%H%M%SZ')
        parts.append(f"UNTIL={until_str}")
    elif count:
        parts.append(f"COUNT={count}")

    return ';'.join(parts)


def calculate_next_occurrence_from_rrule(
    rrule_string: str,
    start_date: datetime,
    after_date: Optional[datetime] = None
) -> Optional[datetime]:
    """Calculate the next occurrence after a given date using an RRULE string.

    Args:
        rrule_string: RFC 5545 RRULE string
        start_date: Original start date of the recurrence
        after_date: Find occurrence after this date (default: now)

    Returns:
        Next occurrence datetime, or None if no more occurrences

    Example:
        >>> rrule_str = 'FREQ=DAILY;INTERVAL=1'
        >>> start = datetime(2026, 1, 1, 9, 0, tzinfo=pytz.UTC)
        >>> after = datetime(2026, 1, 9, 12, 0, tzinfo=pytz.UTC)
        >>> calculate_next_occurrence_from_rrule(rrule_str, start, after)
        datetime(2026, 1, 10, 9, 0, tzinfo=<UTC>)
    """
    try:
        # Parse RRULE
        rule = rrule.rrulestr(rrule_string, dtstart=start_date)

        # Default after_date to now
        if after_date is None:
            after_date = datetime.now(pytz.UTC)

        # Find next occurrence after the given date
        next_occ = rule.after(after_date, inc=False)

        return next_occ

    except Exception as e:
        raise ValueError(f"Failed to calculate next occurrence: {str(e)}") from e
