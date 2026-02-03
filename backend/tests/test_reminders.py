"""Tests for reminder routes"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session
from freezegun import freeze_time

from app.models.task import Task
from app.models.reminder import Reminder


class TestCreateReminder:
    """Tests for POST /api/{user_id}/tasks/{task_id}/reminders"""

    def test_create_reminder_success(self, client: TestClient, mock_jwt: str, session: Session):
        """Test creating a reminder for a task with due date"""
        # Create task with due date
        due_date = datetime.utcnow() + timedelta(hours=2)
        task = Task(
            user_id="user123",
            title="Task with due date",
            due_date=due_date
        )
        session.add(task)
        session.commit()
        session.refresh(task)

        # Create reminder (60 minutes before due date)
        response = client.post(
            f"/api/user123/tasks/{task.id}/reminders",
            json={"offset_minutes": 60, "task_id": task.id},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["task_id"] == task.id
        assert data["user_id"] == "user123"
        assert data["offset_minutes"] == 60
        assert data["delivered"] is False
        assert data["delivery_status"] == "pending"
        assert "remind_at" in data
        assert "id" in data

    def test_create_reminder_task_without_due_date(self, client: TestClient, mock_jwt: str, session: Session):
        """Test creating reminder for task without due date fails"""
        # Create task without due date
        task = Task(user_id="user123", title="Task without due date")
        session.add(task)
        session.commit()
        session.refresh(task)

        # Attempt to create reminder
        response = client.post(
            f"/api/user123/tasks/{task.id}/reminders",
            json={"offset_minutes": 60, "task_id": task.id},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 400
        assert "due date" in response.json()["detail"].lower()

    def test_create_reminder_task_not_found(self, client: TestClient, mock_jwt: str):
        """Test creating reminder for non-existent task"""
        response = client.post(
            "/api/user123/tasks/99999/reminders",
            json={"offset_minutes": 60, "task_id": 99999},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_reminder_invalid_offset(self, client: TestClient, mock_jwt: str, session: Session):
        """Test creating reminder with negative offset fails"""
        # Create task with due date
        due_date = datetime.utcnow() + timedelta(hours=2)
        task = Task(user_id="user123", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        # Attempt with negative offset
        response = client.post(
            f"/api/user123/tasks/{task.id}/reminders",
            json={"offset_minutes": -10, "task_id": task.id},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_create_reminder_unauthorized(self, client: TestClient, mock_jwt: str, session: Session):
        """Test creating reminder for another user's task fails"""
        # Create task for different user
        due_date = datetime.utcnow() + timedelta(hours=2)
        task = Task(user_id="other_user", title="Other user's task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        # Attempt to create reminder as user123
        response = client.post(
            f"/api/user123/tasks/{task.id}/reminders",
            json={"offset_minutes": 60, "task_id": task.id},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 404  # Task not found for this user

    def test_create_reminder_path_user_mismatch(self, client: TestClient, mock_jwt: str, session: Session):
        """Test creating reminder with mismatched path user_id and JWT"""
        due_date = datetime.utcnow() + timedelta(hours=2)
        task = Task(user_id="other_user", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        # Path has other_user but JWT is user123
        response = client.post(
            f"/api/other_user/tasks/{task.id}/reminders",
            json={"offset_minutes": 60, "task_id": task.id},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 403


class TestListReminders:
    """Tests for GET /api/{user_id}/tasks/{task_id}/reminders"""

    def test_list_reminders_success(self, client: TestClient, mock_jwt: str, session: Session):
        """Test listing reminders for a task"""
        # Create task
        due_date = datetime.utcnow() + timedelta(hours=2)
        task = Task(user_id="user123", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        # Create multiple reminders
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

        # List reminders
        response = client.get(
            f"/api/user123/tasks/{task.id}/reminders",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["task_id"] == task.id
        assert data[1]["task_id"] == task.id

    def test_list_reminders_empty(self, client: TestClient, mock_jwt: str, session: Session):
        """Test listing reminders for task with no reminders"""
        # Create task without reminders
        task = Task(user_id="user123", title="Task")
        session.add(task)
        session.commit()
        session.refresh(task)

        response = client.get(
            f"/api/user123/tasks/{task.id}/reminders",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_list_reminders_unauthorized(self, client: TestClient, mock_jwt: str):
        """Test listing reminders with mismatched user_id"""
        response = client.get(
            "/api/other_user/tasks/1/reminders",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 403


class TestDeleteReminder:
    """Tests for DELETE /api/{user_id}/tasks/{task_id}/reminders/{reminder_id}"""

    def test_delete_reminder_success(self, client: TestClient, mock_jwt: str, session: Session):
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
        response = client.delete(
            f"/api/user123/tasks/{task.id}/reminders/{reminder.id}",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 204

        # Verify deleted
        deleted_reminder = session.get(Reminder, reminder.id)
        assert deleted_reminder is None

    def test_delete_reminder_not_found(self, client: TestClient, mock_jwt: str, session: Session):
        """Test deleting non-existent reminder"""
        # Create task
        task = Task(user_id="user123", title="Task")
        session.add(task)
        session.commit()
        session.refresh(task)

        response = client.delete(
            f"/api/user123/tasks/{task.id}/reminders/99999",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 404

    def test_delete_reminder_unauthorized(self, client: TestClient, mock_jwt: str, session: Session):
        """Test deleting another user's reminder"""
        # Create task and reminder for different user
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

        # Attempt to delete as user123
        response = client.delete(
            f"/api/user123/tasks/{task.id}/reminders/{reminder.id}",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 404  # Reminder not found for this user


class TestSnoozeReminder:
    """Tests for PATCH /api/{user_id}/tasks/{task_id}/reminders/{reminder_id}/snooze"""

    @freeze_time("2026-01-15 10:00:00")
    def test_snooze_reminder_success(self, client: TestClient, mock_jwt: str, session: Session):
        """Test snoozing a reminder"""
        # Create task and reminder
        due_date = datetime.utcnow() + timedelta(hours=2)
        task = Task(user_id="user123", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        original_remind_at = datetime.utcnow() + timedelta(minutes=30)
        reminder = Reminder(
            task_id=task.id,
            user_id="user123",
            offset_minutes=90,
            remind_at=original_remind_at,
            delivered=True,
            delivery_status="sent"
        )
        session.add(reminder)
        session.commit()
        session.refresh(reminder)

        # Snooze for 10 minutes
        response = client.patch(
            f"/api/user123/tasks/{task.id}/reminders/{reminder.id}/snooze",
            json={"snooze_minutes": 10},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["delivery_status"] == "snoozed"
        assert data["delivered"] is False
        assert data["delivery_timestamp"] is None

        # Verify remind_at updated
        expected_remind_at = datetime.utcnow() + timedelta(minutes=10)
        actual_remind_at = datetime.fromisoformat(data["remind_at"].replace('Z', '+00:00'))
        # Allow 1 second tolerance
        assert abs((actual_remind_at - expected_remind_at).total_seconds()) < 1

    def test_snooze_reminder_invalid_minutes(self, client: TestClient, mock_jwt: str, session: Session):
        """Test snoozing with invalid snooze_minutes"""
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

        # Attempt with 0 minutes
        response = client.patch(
            f"/api/user123/tasks/{task.id}/reminders/{reminder.id}/snooze",
            json={"snooze_minutes": 0},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 422  # Pydantic validation error

        # Attempt with > 1440 minutes
        response = client.patch(
            f"/api/user123/tasks/{task.id}/reminders/{reminder.id}/snooze",
            json={"snooze_minutes": 2000},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 422

    def test_snooze_reminder_not_found(self, client: TestClient, mock_jwt: str, session: Session):
        """Test snoozing non-existent reminder"""
        # Create task
        task = Task(user_id="user123", title="Task")
        session.add(task)
        session.commit()
        session.refresh(task)

        response = client.patch(
            f"/api/user123/tasks/{task.id}/reminders/99999/snooze",
            json={"snooze_minutes": 10},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 404

    def test_snooze_reminder_unauthorized(self, client: TestClient, mock_jwt: str, session: Session):
        """Test snoozing another user's reminder"""
        # Create task and reminder for different user
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

        # Attempt to snooze as user123
        response = client.patch(
            f"/api/user123/tasks/{task.id}/reminders/{reminder.id}/snooze",
            json={"snooze_minutes": 10},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        assert response.status_code == 404


class TestReminderEdgeCases:
    """Edge case tests for reminder routes"""

    def test_create_reminder_in_past(self, client: TestClient, mock_jwt: str, session: Session):
        """Test creating reminder for task already past due"""
        # Create task with due date in the past
        due_date = datetime.utcnow() - timedelta(hours=1)
        task = Task(user_id="user123", title="Overdue task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        # Create reminder (remind_at will be in the past)
        response = client.post(
            f"/api/user123/tasks/{task.id}/reminders",
            json={"offset_minutes": 30, "task_id": task.id},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )

        # Should succeed but will be processed immediately
        assert response.status_code == 201
        data = response.json()
        assert data["delivered"] is False

    def test_multiple_reminders_same_task(self, client: TestClient, mock_jwt: str, session: Session):
        """Test creating multiple reminders for same task"""
        # Create task
        due_date = datetime.utcnow() + timedelta(hours=2)
        task = Task(user_id="user123", title="Task", due_date=due_date)
        session.add(task)
        session.commit()
        session.refresh(task)

        # Create first reminder
        response1 = client.post(
            f"/api/user123/tasks/{task.id}/reminders",
            json={"offset_minutes": 30, "task_id": task.id},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        assert response1.status_code == 201

        # Create second reminder
        response2 = client.post(
            f"/api/user123/tasks/{task.id}/reminders",
            json={"offset_minutes": 60, "task_id": task.id},
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        assert response2.status_code == 201

        # List reminders
        response = client.get(
            f"/api/user123/tasks/{task.id}/reminders",
            headers={"Authorization": f"Bearer {mock_jwt}"}
        )
        assert len(response.json()) == 2
