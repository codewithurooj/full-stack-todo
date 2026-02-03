"""
Task Creator
Creates new recurring task instances in the database
"""
from datetime import datetime
from typing import Dict, Any, Optional
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError
import logging

from src.models import Task

logger = logging.getLogger(__name__)


async def create_task_instance(
    parent_task_data: Dict[str, Any],
    next_due_date: datetime,
    session: Session
) -> Optional[Task]:
    """
    Create a new recurring task instance in the database

    Args:
        parent_task_data: Data from the completed parent task
        next_due_date: Due date for the new instance
        session: Database session

    Returns:
        Created Task object, or None if creation failed

    Idempotency:
        The database has a unique constraint on (parent_task_id, due_date)
        to prevent duplicate instances. If a duplicate is detected,
        this function returns None and logs the event.
    """
    try:
        # Extract parent task data
        parent_task_id = parent_task_data.get("id")
        user_id = parent_task_data.get("user_id")
        title = parent_task_data.get("title")
        description = parent_task_data.get("description")
        priority = parent_task_data.get("priority", "medium")
        tags = parent_task_data.get("tags", [])
        recurring_pattern = parent_task_data.get("recurring_pattern", "none")
        recurring_interval = parent_task_data.get("recurring_interval", 1)
        recurring_end_date = parent_task_data.get("recurring_end_date")

        # Validate required fields
        if not parent_task_id:
            logger.error("create_task_instance: parent_task_id is missing")
            return None

        if not user_id:
            logger.error("create_task_instance: user_id is missing")
            return None

        # Create new task instance
        new_task = Task(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            tags=tags,
            completed=False,  # New instance starts uncompleted
            due_date=next_due_date,
            parent_task_id=parent_task_id,
            recurring_pattern=recurring_pattern,
            recurring_interval=recurring_interval,
            recurring_end_date=recurring_end_date,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Insert into database
        session.add(new_task)
        session.commit()
        session.refresh(new_task)

        logger.info(
            f"Created recurring task instance: task_id={new_task.id}, "
            f"parent_id={parent_task_id}, user={user_id}, due_date={next_due_date}"
        )

        return new_task

    except IntegrityError as e:
        # Duplicate detected (idempotency constraint)
        session.rollback()
        logger.info(
            f"Duplicate recurring instance detected for parent_id={parent_task_id}, "
            f"due_date={next_due_date} - idempotency working correctly"
        )
        return None

    except Exception as e:
        session.rollback()
        logger.error(
            f"Failed to create recurring task instance: {e}",
            exc_info=True
        )
        return None


def validate_task_data(task_data: Dict[str, Any]) -> bool:
    """
    Validate that task data contains all required fields

    Args:
        task_data: Task data dictionary from Kafka event

    Returns:
        True if valid, False otherwise
    """
    required_fields = ["id", "user_id", "title", "recurring_pattern"]

    for field in required_fields:
        if field not in task_data:
            logger.error(f"validate_task_data: missing required field '{field}'")
            return False

    # Validate recurring_pattern is not 'none'
    if task_data.get("recurring_pattern") == "none":
        logger.debug("validate_task_data: recurring_pattern is 'none', skip processing")
        return False

    return True
