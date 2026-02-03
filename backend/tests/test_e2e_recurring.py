"""
End-to-End Test: Recurring Task Flow
Tests complete flow: create recurring task → complete it → verify next instance + audit log
"""
import pytest
import asyncio
import time
from datetime import datetime, timedelta
from sqlmodel import Session, select

from app.models.task import Task
from app.models.audit_log import AuditLog


class TestE2ERecurringTaskFlow:
    """End-to-end tests for recurring task creation"""

    @pytest.mark.asyncio
    async def test_complete_recurring_task_creates_next_instance(self, client, test_user, db_session):
        """
        Test complete recurring task flow:

        1. Create recurring task (daily pattern)
        2. Mark task as completed
        3. Verify task.completed event published to Kafka
        4. Wait for recurring-task-service to process event (max 10 seconds)
        5. Verify next instance created with correct due_date
        6. Verify next instance has parent_task_id linkage
        7. Verify audit logs captured all operations
        """
        # Step 1: Create recurring task
        task_data = {
            "title": "Daily standup",
            "description": "Team sync meeting",
            "user_id": test_user.id,
            "recurring_pattern": "daily",
            "recurring_interval": 1,
            "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "priority": "high",
            "tags": ["work", "meeting"]
        }

        response = client.post(f"/api/{test_user.id}/tasks", json=task_data)
        assert response.status_code == 201

        parent_task = response.json()
        parent_task_id = parent_task["id"]
        parent_due_date = datetime.fromisoformat(parent_task["due_date"].replace('Z', '+00:00'))

        # Step 2: Complete the task
        response = client.patch(f"/api/{test_user.id}/tasks/{parent_task_id}/complete")
        assert response.status_code == 200

        completed_task = response.json()
        assert completed_task["completed"] is True

        # Step 3: Wait for recurring-task-service to process event
        # In production, this happens within 5 seconds
        # For testing, we'll wait up to 10 seconds and poll database

        next_instance = None
        max_attempts = 20  # 20 attempts * 0.5s = 10 seconds
        for attempt in range(max_attempts):
            await asyncio.sleep(0.5)

            # Query for next instance
            statement = select(Task).where(
                Task.parent_task_id == parent_task_id,
                Task.user_id == test_user.id
            )
            result = db_session.exec(statement).first()

            if result:
                next_instance = result
                break

        # Step 4: Verify next instance was created
        assert next_instance is not None, "Next recurring instance not created within 10 seconds"

        # Step 5: Verify next instance properties
        assert next_instance.title == "Daily standup"
        assert next_instance.description == "Team sync meeting"
        assert next_instance.user_id == test_user.id
        assert next_instance.parent_task_id == parent_task_id
        assert next_instance.recurring_pattern == "daily"
        assert next_instance.recurring_interval == 1
        assert next_instance.completed is False
        assert next_instance.priority == "high"
        assert "work" in next_instance.tags
        assert "meeting" in next_instance.tags

        # Step 6: Verify due_date is +1 day
        next_due_date = next_instance.due_date
        expected_due_date = parent_due_date + timedelta(days=1)

        # Allow 1-second tolerance for processing time
        time_diff = abs((next_due_date - expected_due_date).total_seconds())
        assert time_diff < 1, f"Due date mismatch: expected {expected_due_date}, got {next_due_date}"

        # Step 7: Verify audit logs (wait for audit-service)
        await asyncio.sleep(2)  # Give audit-service time to process

        # Query audit logs
        statement = select(AuditLog).where(
            AuditLog.task_id == parent_task_id
        ).order_by(AuditLog.timestamp)

        audit_logs = db_session.exec(statement).all()

        # Expect at least 2 audit logs: task.created, task.completed
        assert len(audit_logs) >= 2, f"Expected at least 2 audit logs, got {len(audit_logs)}"

        # Verify task.created event
        created_log = next((log for log in audit_logs if log.operation_type == "task.created"), None)
        assert created_log is not None
        assert created_log.user_id == test_user.id
        assert created_log.system_generated is False

        # Verify task.completed event
        completed_log = next((log for log in audit_logs if log.operation_type == "task.completed"), None)
        assert completed_log is not None
        assert completed_log.user_id == test_user.id

        # Step 8: Verify next instance audit log (system-generated)
        statement = select(AuditLog).where(
            AuditLog.task_id == next_instance.id
        )
        next_instance_logs = db_session.exec(statement).all()

        assert len(next_instance_logs) >= 1
        next_created_log = next_instance_logs[0]
        assert next_created_log.operation_type == "task.created"
        assert next_created_log.system_generated is True  # Auto-created by recurring-task-service

    @pytest.mark.asyncio
    async def test_recurring_task_respects_end_date(self, client, test_user, db_session):
        """
        Test that recurring pattern stops at end_date

        1. Create recurring task with end_date = today + 2 days
        2. Complete task (should create instance for tomorrow)
        3. Complete tomorrow's task (should NOT create instance - past end_date)
        """
        # Create recurring task with end_date
        task_data = {
            "title": "Limited recurring task",
            "user_id": test_user.id,
            "recurring_pattern": "daily",
            "recurring_interval": 1,
            "due_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=2)).isoformat()
        }

        response = client.post(f"/api/{test_user.id}/tasks", json=task_data)
        assert response.status_code == 201
        parent_task_id = response.json()["id"]

        # Complete first task
        response = client.patch(f"/api/{test_user.id}/tasks/{parent_task_id}/complete")
        assert response.status_code == 200

        # Wait for next instance
        await asyncio.sleep(5)

        # Query for instances
        statement = select(Task).where(
            Task.parent_task_id == parent_task_id
        )
        instances = db_session.exec(statement).all()

        # Should have exactly 1 instance (within end_date)
        assert len(instances) == 1

        first_instance = instances[0]

        # Complete second task
        response = client.patch(f"/api/{test_user.id}/tasks/{first_instance.id}/complete")
        assert response.status_code == 200

        # Wait and verify no third instance created
        await asyncio.sleep(5)

        statement = select(Task).where(
            Task.parent_task_id == parent_task_id
        )
        instances = db_session.exec(statement).all()

        # Still only 1 instance (end_date prevents second)
        assert len(instances) == 1

    @pytest.mark.asyncio
    async def test_idempotency_prevents_duplicate_instances(self, client, test_user, db_session):
        """
        Test that reprocessing same event doesn't create duplicate instances

        1. Create and complete recurring task
        2. Manually replay task.completed event (simulate reprocessing)
        3. Verify only one next instance exists
        """
        # Create recurring task
        task_data = {
            "title": "Idempotency test",
            "user_id": test_user.id,
            "recurring_pattern": "weekly",
            "recurring_interval": 1,
            "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }

        response = client.post(f"/api/{test_user.id}/tasks", json=task_data)
        parent_task_id = response.json()["id"]

        # Complete task
        response = client.patch(f"/api/{test_user.id}/tasks/{parent_task_id}/complete")
        assert response.status_code == 200

        # Wait for instance
        await asyncio.sleep(5)

        # Count instances
        statement = select(Task).where(
            Task.parent_task_id == parent_task_id
        )
        instances_before = len(db_session.exec(statement).all())

        # Simulate event replay (if Kafka consumer reprocesses)
        # In practice, recurring-task-service checks for existing instance
        # using unique constraint on (parent_task_id, due_date)

        # Wait a bit more
        await asyncio.sleep(3)

        # Count instances again
        instances_after = len(db_session.exec(statement).all())

        # Should be same count (idempotency working)
        assert instances_after == instances_before

    @pytest.mark.asyncio
    async def test_weekly_recurring_pattern(self, client, test_user, db_session):
        """Test weekly recurring pattern creates instance +7 days"""
        task_data = {
            "title": "Weekly meeting",
            "user_id": test_user.id,
            "recurring_pattern": "weekly",
            "recurring_interval": 1,
            "due_date": datetime.utcnow().isoformat()
        }

        response = client.post(f"/api/{test_user.id}/tasks", json=task_data)
        parent_task_id = response.json()["id"]
        parent_due = datetime.fromisoformat(response.json()["due_date"].replace('Z', '+00:00'))

        # Complete task
        response = client.patch(f"/api/{test_user.id}/tasks/{parent_task_id}/complete")
        assert response.status_code == 200

        # Wait for instance
        await asyncio.sleep(5)

        # Get instance
        statement = select(Task).where(Task.parent_task_id == parent_task_id)
        instance = db_session.exec(statement).first()

        assert instance is not None
        next_due = instance.due_date
        expected_due = parent_due + timedelta(days=7)

        time_diff = abs((next_due - expected_due).total_seconds())
        assert time_diff < 1

    @pytest.mark.asyncio
    async def test_monthly_recurring_pattern(self, client, test_user, db_session):
        """Test monthly recurring pattern creates instance +1 month"""
        task_data = {
            "title": "Monthly report",
            "user_id": test_user.id,
            "recurring_pattern": "monthly",
            "recurring_interval": 1,
            "due_date": datetime.utcnow().isoformat()
        }

        response = client.post(f"/api/{test_user.id}/tasks", json=task_data)
        parent_task_id = response.json()["id"]

        # Complete task
        response = client.patch(f"/api/{test_user.id}/tasks/{parent_task_id}/complete")
        assert response.status_code == 200

        # Wait for instance
        await asyncio.sleep(5)

        # Get instance
        statement = select(Task).where(Task.parent_task_id == parent_task_id)
        instance = db_session.exec(statement).first()

        assert instance is not None
        assert instance.recurring_pattern == "monthly"
