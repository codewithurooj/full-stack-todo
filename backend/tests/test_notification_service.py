"""Tests for notification service"""
import pytest
from datetime import datetime, timedelta
from sqlmodel import Session

from app.models.task import Task
from app.models.reminder import Reminder
from app.services.notification_service import (
    format_notification_message,
    send_notification,
    batch_notifications,
    deduplicate_notifications,
    send_batched_notification,
    queue_offline_notification,
    process_user_reminders
)


class TestFormatNotificationMessage:
    """Tests for format_notification_message function"""

    def test_format_notification_message(self):
        """Test formatting notification message"""
        task = Task(
            id=1,
            user_id="user123",
            title="Complete project proposal",
            due_date=datetime(2026, 1, 15, 14, 0)
        )

        reminder = Reminder(
            id=1,
            task_id=1,
            user_id="user123",
            offset_minutes=60,
            remind_at=datetime(2026, 1, 15, 13, 0)
        )

        message = format_notification_message(task, reminder)

        assert "title" in message
        assert "body" in message
        assert "tag" in message
        assert "data" in message
        assert task.title in message["title"]
        assert message["tag"] == "reminder-1"

    def test_format_notification_message_no_due_date(self):
        """Test formatting message for task without due date"""
        task = Task(
            id=1,
            user_id="user123",
            title="Task without due date"
        )

        reminder = Reminder(
            id=1,
            task_id=1,
            user_id="user123",
            offset_minutes=60,
            remind_at=datetime.utcnow()
        )

        message = format_notification_message(task, reminder)

        assert "No due date" in message["body"]


class TestSendNotification:
    """Tests for send_notification function"""

    def test_send_notification(self):
        """Test sending a notification"""
        task = Task(
            id=1,
            user_id="user123",
            title="Task",
            due_date=datetime.utcnow() + timedelta(hours=1)
        )

        reminder = Reminder(
            id=1,
            task_id=1,
            user_id="user123",
            offset_minutes=60,
            remind_at=datetime.utcnow()
        )

        result = send_notification(reminder, task, "user123")

        assert result["status"] == "sent"
        assert "notification_id" in result
        assert "message" in result
        assert "timestamp" in result


class TestBatchNotifications:
    """Tests for batch_notifications function"""

    def test_batch_notifications(self, session: Session):
        """Test batching reminders within time window"""
        task = Task(user_id="user123", title="Task")
        session.add(task)
        session.commit()
        session.refresh(task)

        base_time = datetime.utcnow()

        # Create reminders within 2-minute window
        reminder1 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=60,
            remind_at=base_time,
            delivered=False
        )
        reminder2 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=61,
            remind_at=base_time + timedelta(seconds=30),
            delivered=False
        )
        # This one is outside 2-minute window
        reminder3 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=58,
            remind_at=base_time + timedelta(minutes=3),
            delivered=False
        )

        reminders = [reminder1, reminder2, reminder3]

        batches = batch_notifications(reminders, window_minutes=2)

        # Should have 2 batches
        assert len(batches) == 2
        assert len(batches[0]) == 2  # reminder1 and reminder2
        assert len(batches[1]) == 1  # reminder3

    def test_batch_notifications_empty(self):
        """Test batching empty list"""
        batches = batch_notifications([])

        assert batches == []

    def test_batch_notifications_filters_delivered(self, session: Session):
        """Test that batching filters out delivered reminders"""
        task = Task(user_id="user123", title="Task")
        session.add(task)
        session.commit()
        session.refresh(task)

        base_time = datetime.utcnow()

        # Already delivered
        reminder1 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=60,
            remind_at=base_time,
            delivered=True
        )
        # Not delivered
        reminder2 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=61,
            remind_at=base_time,
            delivered=False
        )

        batches = batch_notifications([reminder1, reminder2])

        # Should only have 1 batch with 1 reminder
        assert len(batches) == 1
        assert len(batches[0]) == 1


class TestDeduplicateNotifications:
    """Tests for deduplicate_notifications function"""

    def test_deduplicate_notifications(self, session: Session):
        """Test deduplicating reminders for same task"""
        task = Task(user_id="user123", title="Task")
        session.add(task)
        session.commit()
        session.refresh(task)

        base_time = datetime.utcnow()

        # Two reminders for same task within 5-minute window
        reminder1 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=60,
            remind_at=base_time
        )
        reminder2 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=57,
            remind_at=base_time + timedelta(minutes=3)
        )

        reminders = [reminder1, reminder2]

        deduped = deduplicate_notifications(reminders, dedup_window_minutes=5)

        # Should keep only the first one
        assert len(deduped) == 1
        assert deduped[0].offset_minutes == 60

    def test_deduplicate_notifications_different_tasks(self, session: Session):
        """Test that different tasks are not deduplicated"""
        task1 = Task(user_id="user123", title="Task 1")
        task2 = Task(user_id="user123", title="Task 2")
        session.add_all([task1, task2])
        session.commit()
        session.refresh(task1)
        session.refresh(task2)

        base_time = datetime.utcnow()

        reminder1 = Reminder(
            task_id=task1.id,
            user_id="user123",
            offset_minutes=60,
            remind_at=base_time
        )
        reminder2 = Reminder(
            task_id=task2.id,
            user_id="user123",
            offset_minutes=60,
            remind_at=base_time
        )

        deduped = deduplicate_notifications([reminder1, reminder2])

        # Should keep both (different tasks)
        assert len(deduped) == 2

    def test_deduplicate_notifications_outside_window(self, session: Session):
        """Test that reminders outside dedup window are kept"""
        task = Task(user_id="user123", title="Task")
        session.add(task)
        session.commit()
        session.refresh(task)

        base_time = datetime.utcnow()

        # Two reminders for same task, but 10 minutes apart
        reminder1 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=60,
            remind_at=base_time
        )
        reminder2 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=50,
            remind_at=base_time + timedelta(minutes=10)
        )

        deduped = deduplicate_notifications([reminder1, reminder2], dedup_window_minutes=5)

        # Should keep both (outside window)
        assert len(deduped) == 2


class TestSendBatchedNotification:
    """Tests for send_batched_notification function"""

    def test_send_batched_notification(self, session: Session):
        """Test sending batched notification"""
        task1 = Task(id=1, user_id="user123", title="Task 1")
        task2 = Task(id=2, user_id="user123", title="Task 2")

        reminder1 = Reminder(
            task_id=1,
            user_id="user123",
            offset_minutes=60,
            remind_at=datetime.utcnow()
        )
        reminder2 = Reminder(
            task_id=2,
            user_id="user123",
            offset_minutes=60,
            remind_at=datetime.utcnow()
        )

        batch = [reminder1, reminder2]
        tasks = {1: task1, 2: task2}

        result = send_batched_notification(batch, tasks, "user123")

        assert result["status"] == "sent"
        assert result["reminder_count"] == 2
        assert "notification_id" in result

    def test_send_batched_notification_empty(self):
        """Test sending empty batch"""
        result = send_batched_notification([], {}, "user123")

        assert result["status"] == "skipped"
        assert result["reason"] == "empty_batch"


class TestQueueOfflineNotification:
    """Tests for queue_offline_notification function"""

    def test_queue_offline_notification(self):
        """Test queueing offline notification"""
        task = Task(id=1, user_id="user123", title="Task")
        reminder = Reminder(
            id=1,
            task_id=1,
            user_id="user123",
            offset_minutes=60,
            remind_at=datetime.utcnow()
        )

        result = queue_offline_notification(reminder, task, reason="user_offline")

        assert result["status"] == "queued"
        assert result["reminder_id"] == 1
        assert result["task_id"] == 1
        assert result["reason"] == "user_offline"


class TestProcessUserReminders:
    """Tests for process_user_reminders function"""

    def test_process_user_reminders_single(self, session: Session):
        """Test processing single reminder"""
        task = Task(id=1, user_id="user123", title="Task")
        reminder = Reminder(
            id=1,
            task_id=1,
            user_id="user123",
            offset_minutes=60,
            remind_at=datetime.utcnow(),
            delivered=False
        )

        tasks = {1: task}
        reminders = [reminder]

        result = process_user_reminders(reminders, tasks, "user123", enable_batching=False)

        assert result["user_id"] == "user123"
        assert result["reminders_processed"] == 1
        assert result["notifications_sent"] == 1
        assert result["batches"] == 0

    def test_process_user_reminders_batched(self, session: Session):
        """Test processing multiple reminders with batching"""
        task1 = Task(id=1, user_id="user123", title="Task 1")
        task2 = Task(id=2, user_id="user123", title="Task 2")

        base_time = datetime.utcnow()

        reminder1 = Reminder(
            id=1,
            task_id=1,
            user_id="user123",
            offset_minutes=60,
            remind_at=base_time,
            delivered=False
        )
        reminder2 = Reminder(
            id=2,
            task_id=2,
            user_id="user123",
            offset_minutes=61,
            remind_at=base_time + timedelta(seconds=30),
            delivered=False
        )

        tasks = {1: task1, 2: task2}
        reminders = [reminder1, reminder2]

        result = process_user_reminders(
            reminders,
            tasks,
            "user123",
            enable_batching=True,
            enable_deduplication=True
        )

        assert result["user_id"] == "user123"
        assert result["reminders_processed"] == 2
        # With batching, should send 1 batched notification
        assert result["batches"] > 0

    def test_process_user_reminders_empty(self):
        """Test processing empty reminder list"""
        result = process_user_reminders([], {}, "user123")

        assert result["reminders_processed"] == 0
        assert result["notifications_sent"] == 0

    def test_process_user_reminders_deduplication(self, session: Session):
        """Test that deduplication works in processing"""
        task = Task(id=1, user_id="user123", title="Task")

        base_time = datetime.utcnow()

        # Two reminders for same task within dedup window
        reminder1 = Reminder(
            id=1,
            task_id=1,
            user_id="user123",
            offset_minutes=60,
            remind_at=base_time,
            delivered=False
        )
        reminder2 = Reminder(
            id=2,
            task_id=1,
            user_id="user123",
            offset_minutes=57,
            remind_at=base_time + timedelta(minutes=2),
            delivered=False
        )

        tasks = {1: task}
        reminders = [reminder1, reminder2]

        result = process_user_reminders(
            reminders,
            tasks,
            "user123",
            enable_batching=False,
            enable_deduplication=True
        )

        # Should process only 1 after deduplication
        assert result["reminders_processed"] == 1

    def test_process_user_reminders_missing_task(self, session: Session):
        """Test processing reminder with missing task"""
        reminder = Reminder(
            id=1,
            task_id=999,  # Non-existent task
            user_id="user123",
            offset_minutes=60,
            remind_at=datetime.utcnow(),
            delivered=False
        )

        tasks = {}  # Empty tasks dict
        reminders = [reminder]

        result = process_user_reminders(reminders, tasks, "user123", enable_batching=False)

        # Should still process but not send notification
        assert result["notifications_sent"] == 0
