"""Tests for reminder service"""
import pytest
from datetime import datetime, timedelta
from sqlmodel import Session
from freezegun import freeze_time

from app.models.task import Task
from app.models.reminder import Reminder
from app.services.reminder_service import (
    calculate_remind_at,
    create_reminder,
    get_task_reminders,
    delete_reminder,
    snooze_reminder,
    get_pending_reminders,
    mark_reminder_delivered,
    get_failed_reminders
)


class TestCalculateRemindAt:
    """Tests for calculate_remind_at function"""

    def test_calculate_remind_at(self):
        """Test calculating remind_at time"""
        due_date = datetime(2026, 1, 15, 10, 0)  # 10:00 AM
        remind_at = calculate_remind_at(due_date, 60)  # 1 hour before

        assert remind_at == datetime(2026, 1, 15, 9, 0)  # 9:00 AM

    def test_calculate_remind_at_30_minutes(self):
        """Test 30 minute offset"""
        due_date = datetime(2026, 1, 15, 14, 30)
        remind_at = calculate_remind_at(due_date, 30)

        assert remind_at == datetime(2026, 1, 15, 14, 0)

    def test_calculate_remind_at_zero_offset(self):
        """Test zero offset (remind at due date)"""
        due_date = datetime(2026, 1, 15, 12, 0)
        remind_at = calculate_remind_at(due_date, 0)

        assert remind_at == due_date


class TestCreateReminder:
    """Tests for create_reminder function"""

    def test_create_reminder_success(self, session: Session):
        """Test creating a reminder"""
        # Create task
        due_date = datetime.utcnow() + timedelta(hours=2)
        task = Task(user_id="user123", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        # Create reminder
        reminder = create_reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=60,
            session=session
        )

        assert reminder is not None
        assert reminder.task_id == task.id
        assert reminder.user_id == "user123"
        assert reminder.offset_minutes == 60
        assert reminder.delivered is False
        assert reminder.delivery_status == "pending"

        # Verify remind_at calculated correctly
        expected_remind_at = due_date - timedelta(minutes=60)
        assert abs((reminder.remind_at - expected_remind_at).total_seconds()) < 1

    def test_create_reminder_task_not_found(self, session: Session):
        """Test creating reminder for non-existent task"""
        reminder = create_reminder(
            task_id=99999,
            user_id="user123",
            offset_minutes=60,
            session=session
        )

        assert reminder is None

    def test_create_reminder_no_due_date(self, session: Session):
        """Test creating reminder for task without due date"""
        # Create task without due date
        task = Task(user_id="user123", title="Task")
        session.add(task)
        session.commit()
        session.refresh(task)

        # Attempt to create reminder
        with pytest.raises(ValueError, match="due date"):
            create_reminder(
                task_id=task.id,
                user_id="user123",
                offset_minutes=60,
                session=session
            )

    def test_create_reminder_negative_offset(self, session: Session):
        """Test creating reminder with negative offset"""
        due_date = datetime.utcnow() + timedelta(hours=2)
        task = Task(user_id="user123", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        with pytest.raises(ValueError, match="non-negative"):
            create_reminder(
                task_id=task.id,
                user_id="user123",
                offset_minutes=-10,
                session=session
            )

    def test_create_reminder_unauthorized(self, session: Session):
        """Test creating reminder for another user's task"""
        due_date = datetime.utcnow() + timedelta(hours=2)
        task = Task(user_id="other_user", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        reminder = create_reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=60,
            session=session
        )

        assert reminder is None


class TestGetTaskReminders:
    """Tests for get_task_reminders function"""

    def test_get_task_reminders(self, session: Session):
        """Test getting reminders for a task"""
        # Create task
        due_date = datetime.utcnow() + timedelta(hours=2)
        task = Task(user_id="user123", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        # Create reminders
        reminder1 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=30,
            remind_at=due_date - timedelta(minutes=30)
        )
        reminder2 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=60,
            remind_at=due_date - timedelta(minutes=60)
        )
        session.add(reminder1)
        session.add(reminder2)
        session.commit()

        # Get reminders
        reminders = get_task_reminders(task.id, "user123", session)

        assert len(reminders) == 2
        # Should be sorted by remind_at ascending
        assert reminders[0].offset_minutes == 60  # Earlier reminder
        assert reminders[1].offset_minutes == 30

    def test_get_task_reminders_empty(self, session: Session):
        """Test getting reminders for task with no reminders"""
        task = Task(user_id="user123", title="Task")
        session.add(task)
        session.commit()
        session.refresh(task)

        reminders = get_task_reminders(task.id, "user123", session)

        assert reminders == []


class TestDeleteReminder:
    """Tests for delete_reminder function"""

    def test_delete_reminder_success(self, session: Session):
        """Test deleting a reminder"""
        # Create task and reminder
        due_date = datetime.utcnow() + timedelta(hours=2)
        task = Task(user_id="user123", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        reminder = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=60,
            remind_at=due_date - timedelta(minutes=60)
        )
        session.add(reminder)
        session.commit()
        session.refresh(reminder)

        # Delete reminder
        result = delete_reminder(reminder.id, "user123", session)

        assert result is True

        # Verify deleted
        deleted = session.get(Reminder, reminder.id)
        assert deleted is None

    def test_delete_reminder_not_found(self, session: Session):
        """Test deleting non-existent reminder"""
        result = delete_reminder(99999, "user123", session)

        assert result is False

    def test_delete_reminder_unauthorized(self, session: Session):
        """Test deleting another user's reminder"""
        due_date = datetime.utcnow() + timedelta(hours=2)
        task = Task(user_id="other_user", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        reminder = Reminder(
            task_id=task.id,
            user_id="other_user",
            offset_minutes=60,
            remind_at=due_date - timedelta(minutes=60)
        )
        session.add(reminder)
        session.commit()
        session.refresh(reminder)

        result = delete_reminder(reminder.id, "user123", session)

        assert result is False


class TestSnoozeReminder:
    """Tests for snooze_reminder function"""

    @freeze_time("2026-01-15 10:00:00")
    def test_snooze_reminder_success(self, session: Session):
        """Test snoozing a reminder"""
        # Create task and reminder
        due_date = datetime.utcnow() + timedelta(hours=2)
        task = Task(user_id="user123", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        reminder = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=90,
            remind_at=datetime.utcnow() + timedelta(minutes=30),
            delivered=True,
            delivery_status="sent"
        )
        session.add(reminder)
        session.commit()
        session.refresh(reminder)

        # Snooze for 10 minutes
        updated = snooze_reminder(reminder.id, "user123", 10, session)

        assert updated is not None
        assert updated.delivery_status == "snoozed"
        assert updated.delivered is False
        assert updated.delivery_timestamp is None

        # Verify remind_at updated
        expected = datetime.utcnow() + timedelta(minutes=10)
        assert abs((updated.remind_at - expected).total_seconds()) < 1

    def test_snooze_reminder_invalid_minutes(self, session: Session):
        """Test snoozing with invalid snooze_minutes"""
        due_date = datetime.utcnow() + timedelta(hours=2)
        task = Task(user_id="user123", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        reminder = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=60,
            remind_at=due_date - timedelta(minutes=60)
        )
        session.add(reminder)
        session.commit()
        session.refresh(reminder)

        # Test with 0 minutes
        with pytest.raises(ValueError, match="between 1 and 1440"):
            snooze_reminder(reminder.id, "user123", 0, session)

        # Test with > 1440 minutes
        with pytest.raises(ValueError, match="between 1 and 1440"):
            snooze_reminder(reminder.id, "user123", 2000, session)

    def test_snooze_reminder_not_found(self, session: Session):
        """Test snoozing non-existent reminder"""
        result = snooze_reminder(99999, "user123", 10, session)

        assert result is None


class TestGetPendingReminders:
    """Tests for get_pending_reminders function"""

    @freeze_time("2026-01-15 10:00:00")
    def test_get_pending_reminders(self, session: Session):
        """Test getting pending reminders"""
        current_time = datetime.utcnow()

        # Create task
        task = Task(user_id="user123", title="Task", due_date=current_time + timedelta(hours=1))
        session.add(task)
        session.commit()
        session.refresh(task)

        # Create pending reminder (due now)
        reminder1 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=60,
            remind_at=current_time - timedelta(minutes=1),  # 1 minute ago
            delivered=False
        )

        # Create pending reminder (due in 3 minutes)
        reminder2 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=57,
            remind_at=current_time + timedelta(minutes=3),
            delivered=False
        )

        # Create already delivered reminder
        reminder3 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=120,
            remind_at=current_time - timedelta(minutes=5),
            delivered=True
        )

        # Create future reminder (beyond lookahead)
        reminder4 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=0,
            remind_at=current_time + timedelta(minutes=10),
            delivered=False
        )

        session.add_all([reminder1, reminder2, reminder3, reminder4])
        session.commit()

        # Get pending reminders (5 minute lookahead)
        pending = get_pending_reminders(session, current_time, lookahead_minutes=5)

        # Should only get reminder1 and reminder2
        assert len(pending) == 2
        assert reminder1.id in [r.id for r in pending]
        assert reminder2.id in [r.id for r in pending]

    def test_get_pending_reminders_empty(self, session: Session):
        """Test getting pending reminders when none exist"""
        pending = get_pending_reminders(session)

        assert pending == []


class TestMarkReminderDelivered:
    """Tests for mark_reminder_delivered function"""

    def test_mark_reminder_delivered_success(self, session: Session):
        """Test marking reminder as delivered"""
        # Create reminder
        due_date = datetime.utcnow() + timedelta(hours=1)
        task = Task(user_id="user123", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        reminder = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=60,
            remind_at=due_date - timedelta(minutes=60),
            delivered=False
        )
        session.add(reminder)
        session.commit()
        session.refresh(reminder)

        # Mark as delivered
        updated = mark_reminder_delivered(
            reminder.id,
            session,
            notification_id="notif-123",
            success=True
        )

        assert updated is not None
        assert updated.delivered is True
        assert updated.delivery_status == "sent"
        assert updated.notification_id == "notif-123"
        assert updated.delivery_timestamp is not None

    def test_mark_reminder_delivered_failed(self, session: Session):
        """Test marking reminder as failed"""
        due_date = datetime.utcnow() + timedelta(hours=1)
        task = Task(user_id="user123", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        reminder = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=60,
            remind_at=due_date - timedelta(minutes=60)
        )
        session.add(reminder)
        session.commit()
        session.refresh(reminder)

        # Mark as failed
        updated = mark_reminder_delivered(reminder.id, session, success=False)

        assert updated is not None
        assert updated.delivered is False
        assert updated.delivery_status == "failed"

    def test_mark_reminder_delivered_not_found(self, session: Session):
        """Test marking non-existent reminder"""
        result = mark_reminder_delivered(99999, session)

        assert result is None


class TestGetFailedReminders:
    """Tests for get_failed_reminders function"""

    def test_get_failed_reminders(self, session: Session):
        """Test getting failed reminders"""
        due_date = datetime.utcnow() + timedelta(hours=1)
        task = Task(user_id="user123", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        # Create failed reminder
        reminder1 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=60,
            remind_at=due_date - timedelta(minutes=60),
            delivered=False,
            delivery_status="failed"
        )

        # Create successful reminder
        reminder2 = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=30,
            remind_at=due_date - timedelta(minutes=30),
            delivered=True,
            delivery_status="sent"
        )

        session.add_all([reminder1, reminder2])
        session.commit()

        # Get failed reminders
        failed = get_failed_reminders(session)

        assert len(failed) == 1
        assert failed[0].id == reminder1.id

    def test_get_failed_reminders_empty(self, session: Session):
        """Test getting failed reminders when none exist"""
        failed = get_failed_reminders(session)

        assert failed == []
