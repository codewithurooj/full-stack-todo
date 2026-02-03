"""Recurring task instance generator job.

This job runs periodically to generate new instances of recurring tasks
that are due for creation.
"""

from datetime import datetime
import logging
import pytz

from app.database import engine
from sqlmodel import Session
from app.services.recurring_service import (
    get_recurring_tasks_due,
    generate_recurring_instances
)

logger = logging.getLogger(__name__)


def generate_due_instances():
    """Generate instances for recurring tasks that are due.

    This function is called by APScheduler every 1 minute.
    It finds all recurring tasks where next_occurrence <= now
    and generates the next instance for each.
    """
    logger.info("Running recurring task generator job")

    with Session(engine) as session:
        try:
            # Get tasks that need instances generated
            tasks_due = get_recurring_tasks_due(session)

            if not tasks_due:
                logger.debug("No recurring tasks due for instance generation")
                return

            logger.info(f"Found {len(tasks_due)} tasks due for instance generation")

            generated_count = 0
            failed_count = 0

            for task in tasks_due:
                try:
                    # Generate next instance
                    instance = generate_recurring_instances(task.id, session)

                    if instance:
                        generated_count += 1
                        logger.debug(
                            f"Generated instance {instance.id} for task {task.id}, "
                            f"due_date={instance.due_date}"
                        )
                    else:
                        logger.debug(f"No more instances for task {task.id}")

                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"Failed to generate instance for task {task.id}: {e}",
                        exc_info=True
                    )

            logger.info(
                f"Recurring task generator completed: "
                f"generated={generated_count}, failed={failed_count}"
            )

        except Exception as e:
            logger.error(f"Recurring task generator job failed: {e}", exc_info=True)


def register_recurring_generator(scheduler):
    """Register recurring generator job with scheduler.

    Args:
        scheduler: APScheduler instance

    This job runs every 1 minute to check for recurring tasks
    that need new instances generated.
    """
    from app.jobs.scheduler import add_job

    add_job(
        func=generate_due_instances,
        trigger='interval',
        minutes=1,
        id='recurring_generator',
        replace_existing=True
    )

    logger.info("Registered recurring_generator job (every 1 minute)")
