"""
Recurrence Calculation Logic
Calculates next due date for recurring tasks
"""
from datetime import datetime, timedelta
from typing import Optional
from dateutil.relativedelta import relativedelta
import logging

logger = logging.getLogger(__name__)


def calculate_next_due_date(
    current_due_date: datetime,
    recurring_pattern: str,
    recurring_interval: int,
    end_date: Optional[datetime] = None
) -> Optional[datetime]:
    """
    Calculate the next due date for a recurring task

    Args:
        current_due_date: Current task due date
        recurring_pattern: Recurrence pattern (daily, weekly, monthly)
        recurring_interval: Interval count (e.g., 2 for "every 2 days")
        end_date: Optional end date - stop recurring after this date

    Returns:
        Next due date, or None if recurring pattern has ended

    Examples:
        >>> calculate_next_due_date(datetime(2026, 1, 13), "daily", 1, None)
        datetime(2026, 1, 14, 0, 0)

        >>> calculate_next_due_date(datetime(2026, 1, 13), "weekly", 2, None)
        datetime(2026, 1, 27, 0, 0)

        >>> calculate_next_due_date(datetime(2026, 1, 31), "monthly", 1, None)
        datetime(2026, 2, 28, 0, 0)  # Handles month-end correctly
    """
    if not current_due_date:
        logger.warning("calculate_next_due_date: current_due_date is None")
        return None

    if recurring_pattern == "none":
        logger.debug("calculate_next_due_date: pattern is 'none', no recurrence")
        return None

    if recurring_interval <= 0:
        logger.warning(f"Invalid recurring_interval: {recurring_interval}, must be > 0")
        return None

    # Calculate next date based on pattern
    try:
        if recurring_pattern == "daily":
            next_date = current_due_date + timedelta(days=recurring_interval)

        elif recurring_pattern == "weekly":
            next_date = current_due_date + timedelta(weeks=recurring_interval)

        elif recurring_pattern == "monthly":
            # Use dateutil.relativedelta to handle month-end dates correctly
            # e.g., Jan 31 + 1 month = Feb 28 (not March 3)
            next_date = current_due_date + relativedelta(months=recurring_interval)

        else:
            logger.error(f"Unknown recurring_pattern: {recurring_pattern}")
            return None

        # Check if next date exceeds end_date
        if end_date and next_date > end_date:
            logger.info(
                f"Next due date {next_date} exceeds end_date {end_date}, "
                f"stopping recurrence"
            )
            return None

        logger.debug(
            f"Calculated next due date: {next_date} "
            f"(pattern={recurring_pattern}, interval={recurring_interval})"
        )
        return next_date

    except Exception as e:
        logger.error(f"Error calculating next due date: {e}", exc_info=True)
        return None


def should_create_instance(
    current_due_date: datetime,
    end_date: Optional[datetime] = None
) -> bool:
    """
    Check if a recurring instance should be created

    Args:
        current_due_date: Proposed due date for next instance
        end_date: Optional end date for recurrence

    Returns:
        True if instance should be created, False otherwise
    """
    # Don't create instances with past due dates (already overdue)
    # Allow small grace period of 1 day for timezone differences
    grace_period = timedelta(days=1)
    if current_due_date < (datetime.utcnow() - grace_period):
        logger.warning(
            f"Due date {current_due_date} is too far in the past, skipping instance"
        )
        return False

    # Check end_date constraint
    if end_date and current_due_date > end_date:
        logger.info(f"Due date {current_due_date} exceeds end_date {end_date}")
        return False

    return True
