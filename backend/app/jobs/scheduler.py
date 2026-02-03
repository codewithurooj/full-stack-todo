"""APScheduler configuration and management"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Job stores (using in-memory for MVP)
jobstores = {
    'default': MemoryJobStore()
}

# Executors (thread pool for I/O-bound tasks)
executors = {
    'default': ThreadPoolExecutor(max_workers=10)
}

# Job defaults
job_defaults = {
    'coalesce': True,  # Combine multiple pending executions into one
    'max_instances': 1,  # Only one instance of each job running at a time
    'misfire_grace_time': 60  # Allow 60 seconds grace period for missed jobs
}

# Create scheduler instance
scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='UTC'
)


def start_scheduler():
    """
    Start the APScheduler.

    This should be called during application startup.
    """
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started successfully")
        logger.info(f"Scheduler timezone: {scheduler.timezone}")
        logger.info(f"Scheduler state: {scheduler.state}")
    else:
        logger.warning("Scheduler already running")


def shutdown_scheduler():
    """
    Shutdown the APScheduler gracefully.

    This should be called during application shutdown.
    """
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler shut down successfully")
    else:
        logger.warning("Scheduler not running")


def add_job(func, trigger, **kwargs):
    """
    Add a job to the scheduler.

    Args:
        func: Function to execute
        trigger: Trigger type ('interval', 'cron', 'date')
        **kwargs: Additional job parameters (id, seconds, minutes, etc.)

    Returns:
        Job instance

    Example:
        >>> add_job(my_function, 'interval', seconds=30, id='my_job')
    """
    job = scheduler.add_job(func, trigger, **kwargs)
    logger.info(f"Job added: {job.id}, trigger={trigger}, next_run={job.next_run_time}")
    return job


def remove_job(job_id):
    """
    Remove a job from the scheduler.

    Args:
        job_id: Job identifier

    Example:
        >>> remove_job('my_job')
    """
    scheduler.remove_job(job_id)
    logger.info(f"Job removed: {job_id}")


def get_jobs():
    """
    Get all scheduled jobs.

    Returns:
        List of job instances
    """
    return scheduler.get_jobs()


def get_job(job_id):
    """
    Get a specific job by ID.

    Args:
        job_id: Job identifier

    Returns:
        Job instance or None
    """
    return scheduler.get_job(job_id)


def pause_job(job_id):
    """
    Pause a job.

    Args:
        job_id: Job identifier
    """
    scheduler.pause_job(job_id)
    logger.info(f"Job paused: {job_id}")


def resume_job(job_id):
    """
    Resume a paused job.

    Args:
        job_id: Job identifier
    """
    scheduler.resume_job(job_id)
    logger.info(f"Job resumed: {job_id}")


# For testing purposes
def is_running():
    """Check if scheduler is running."""
    return scheduler.running


def get_scheduler():
    """Get scheduler instance (for testing)."""
    return scheduler
