"""
Reminder Scheduler Service
Feature: 012-dapr-integration
Purpose: Schedule and manage task reminder jobs using Dapr Jobs API
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel

from app.config import settings
from app.services.dapr_client import get_dapr_client

logger = logging.getLogger(__name__)

# Reminder intervals before due date
REMINDER_24H = timedelta(hours=24)
REMINDER_1H = timedelta(hours=1)


class ReminderJobPayload(BaseModel):
    """Payload for reminder jobs"""
    task_id: int
    user_id: str
    title: str
    due_date: Optional[str] = None
    notification_type: str = "browser"
    reminder_type: str  # "24h" or "1h"


class ReminderScheduler:
    """
    Service for scheduling task reminders via Dapr Jobs API.

    Reminders are scheduled at:
    - 24 hours before due date
    - 1 hour before due date
    """

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy load Dapr client"""
        if self._client is None:
            self._client = get_dapr_client()
        return self._client

    def _get_job_name(self, task_id: int, reminder_type: str) -> str:
        """Generate job name for a reminder"""
        return f"reminder-{task_id}-{reminder_type}"

    async def schedule_task_reminders(
        self,
        task_id: int,
        user_id: str,
        title: str,
        due_date: datetime
    ) -> Dict[str, bool]:
        """
        Schedule reminders for a task with a due date.

        Creates two reminder jobs:
        - 24 hours before due date
        - 1 hour before due date

        Args:
            task_id: Task identifier
            user_id: User who owns the task
            title: Task title
            due_date: Task due date (UTC)

        Returns:
            Dict with job names and success status
        """
        results = {}
        now = datetime.now(timezone.utc)

        # Ensure due_date is timezone-aware
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)

        # Schedule 24-hour reminder
        reminder_24h_time = due_date - REMINDER_24H
        if reminder_24h_time > now:
            job_name_24h = self._get_job_name(task_id, "24h")
            payload_24h = ReminderJobPayload(
                task_id=task_id,
                user_id=user_id,
                title=title,
                due_date=due_date.isoformat(),
                reminder_type="24h"
            )
            success = await self.client.schedule_job(
                job_name=job_name_24h,
                due_time=reminder_24h_time,
                data=payload_24h.model_dump(),
                ttl="25h"  # Job expires after 25 hours if not executed
            )
            results[job_name_24h] = success
            if success:
                logger.info(f"Scheduled 24h reminder for task {task_id} at {reminder_24h_time}")
            else:
                logger.warning(f"Failed to schedule 24h reminder for task {task_id}")
        else:
            logger.debug(f"24h reminder time already passed for task {task_id}")

        # Schedule 1-hour reminder
        reminder_1h_time = due_date - REMINDER_1H
        if reminder_1h_time > now:
            job_name_1h = self._get_job_name(task_id, "1h")
            payload_1h = ReminderJobPayload(
                task_id=task_id,
                user_id=user_id,
                title=title,
                due_date=due_date.isoformat(),
                reminder_type="1h"
            )
            success = await self.client.schedule_job(
                job_name=job_name_1h,
                due_time=reminder_1h_time,
                data=payload_1h.model_dump(),
                ttl="2h"  # Job expires after 2 hours if not executed
            )
            results[job_name_1h] = success
            if success:
                logger.info(f"Scheduled 1h reminder for task {task_id} at {reminder_1h_time}")
            else:
                logger.warning(f"Failed to schedule 1h reminder for task {task_id}")
        else:
            logger.debug(f"1h reminder time already passed for task {task_id}")

        return results

    async def cancel_task_reminders(self, task_id: int) -> Dict[str, bool]:
        """
        Cancel all reminders for a task.

        Called when:
        - Task is completed
        - Task is deleted

        Args:
            task_id: Task identifier

        Returns:
            Dict with job names and cancellation status
        """
        results = {}

        # Cancel 24-hour reminder
        job_name_24h = self._get_job_name(task_id, "24h")
        success_24h = await self.client.cancel_job(job_name_24h)
        results[job_name_24h] = success_24h
        logger.info(f"Cancelled 24h reminder for task {task_id}: {success_24h}")

        # Cancel 1-hour reminder
        job_name_1h = self._get_job_name(task_id, "1h")
        success_1h = await self.client.cancel_job(job_name_1h)
        results[job_name_1h] = success_1h
        logger.info(f"Cancelled 1h reminder for task {task_id}: {success_1h}")

        return results

    async def reschedule_task_reminders(
        self,
        task_id: int,
        user_id: str,
        title: str,
        new_due_date: datetime
    ) -> Dict[str, bool]:
        """
        Reschedule reminders when a task's due date is updated.

        First cancels existing reminders, then schedules new ones.

        Args:
            task_id: Task identifier
            user_id: User who owns the task
            title: Task title
            new_due_date: New due date (UTC)

        Returns:
            Dict with all job operations and their status
        """
        # Cancel existing reminders
        cancel_results = await self.cancel_task_reminders(task_id)

        # Schedule new reminders
        schedule_results = await self.schedule_task_reminders(
            task_id=task_id,
            user_id=user_id,
            title=title,
            due_date=new_due_date
        )

        # Combine results
        results = {
            "cancelled": cancel_results,
            "scheduled": schedule_results
        }

        logger.info(f"Rescheduled reminders for task {task_id} to {new_due_date}")
        return results


# In-memory fallback storage for when Dapr Jobs API is unavailable (T043)
# Maps job_name -> (due_time, payload)
_fallback_jobs: Dict[str, tuple[datetime, Dict[str, Any]]] = {}


class FallbackReminderScheduler:
    """
    Fallback scheduler when Dapr Jobs API is unavailable.

    Uses in-memory storage with cron-style polling pattern.
    This is intended for local development without Dapr.
    """

    def _get_job_name(self, task_id: int, reminder_type: str) -> str:
        return f"reminder-{task_id}-{reminder_type}"

    async def schedule_task_reminders(
        self,
        task_id: int,
        user_id: str,
        title: str,
        due_date: datetime
    ) -> Dict[str, bool]:
        """Schedule reminders in fallback storage"""
        results = {}
        now = datetime.now(timezone.utc)

        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)

        # 24-hour reminder
        reminder_24h_time = due_date - REMINDER_24H
        if reminder_24h_time > now:
            job_name = self._get_job_name(task_id, "24h")
            payload = ReminderJobPayload(
                task_id=task_id,
                user_id=user_id,
                title=title,
                due_date=due_date.isoformat(),
                reminder_type="24h"
            )
            _fallback_jobs[job_name] = (reminder_24h_time, payload.model_dump())
            results[job_name] = True
            logger.info(f"[Fallback] Scheduled 24h reminder for task {task_id}")

        # 1-hour reminder
        reminder_1h_time = due_date - REMINDER_1H
        if reminder_1h_time > now:
            job_name = self._get_job_name(task_id, "1h")
            payload = ReminderJobPayload(
                task_id=task_id,
                user_id=user_id,
                title=title,
                due_date=due_date.isoformat(),
                reminder_type="1h"
            )
            _fallback_jobs[job_name] = (reminder_1h_time, payload.model_dump())
            results[job_name] = True
            logger.info(f"[Fallback] Scheduled 1h reminder for task {task_id}")

        return results

    async def cancel_task_reminders(self, task_id: int) -> Dict[str, bool]:
        """Cancel reminders from fallback storage"""
        results = {}
        for reminder_type in ["24h", "1h"]:
            job_name = self._get_job_name(task_id, reminder_type)
            if job_name in _fallback_jobs:
                del _fallback_jobs[job_name]
                results[job_name] = True
                logger.info(f"[Fallback] Cancelled {reminder_type} reminder for task {task_id}")
            else:
                results[job_name] = True  # Job doesn't exist, consider it cancelled
        return results

    async def reschedule_task_reminders(
        self,
        task_id: int,
        user_id: str,
        title: str,
        new_due_date: datetime
    ) -> Dict[str, bool]:
        """Reschedule reminders in fallback storage"""
        cancel_results = await self.cancel_task_reminders(task_id)
        schedule_results = await self.schedule_task_reminders(
            task_id, user_id, title, new_due_date
        )
        return {"cancelled": cancel_results, "scheduled": schedule_results}

    @staticmethod
    def get_pending_reminders() -> list[tuple[str, Dict[str, Any]]]:
        """
        Get all reminders that should be triggered now.

        Used by cron job to poll for due reminders.
        Returns list of (job_name, payload) tuples.
        """
        now = datetime.now(timezone.utc)
        due_reminders = []

        for job_name, (due_time, payload) in list(_fallback_jobs.items()):
            if due_time <= now:
                due_reminders.append((job_name, payload))
                del _fallback_jobs[job_name]

        return due_reminders


# Global reminder scheduler instance
_reminder_scheduler: Optional[ReminderScheduler] = None
_fallback_scheduler: Optional[FallbackReminderScheduler] = None


def get_reminder_scheduler():
    """Get the appropriate reminder scheduler based on Dapr availability"""
    global _reminder_scheduler, _fallback_scheduler

    if settings.DAPR_ENABLED:
        if _reminder_scheduler is None:
            _reminder_scheduler = ReminderScheduler()
        return _reminder_scheduler
    else:
        # Use fallback scheduler when Dapr is not available
        if _fallback_scheduler is None:
            _fallback_scheduler = FallbackReminderScheduler()
            logger.info("Using fallback reminder scheduler (Dapr unavailable)")
        return _fallback_scheduler
