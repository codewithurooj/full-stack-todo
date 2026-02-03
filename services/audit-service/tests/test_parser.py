"""
Test Event Parser
Tests event validation and parsing logic
"""
import pytest
from datetime import datetime
from uuid import UUID, uuid4

from src.parser import parse_event_to_audit_log, validate_event


class TestValidateEvent:
    """Test event validation logic"""

    def test_validate_event_valid(self):
        """Test valid event passes validation"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "task.created",
            "timestamp": "2026-01-13T12:00:00Z",
            "user_id": "user123",
            "task_id": 42
        }

        assert validate_event(event) is True

    def test_validate_event_missing_event_id(self):
        """Test event missing event_id fails validation"""
        event = {
            "event_type": "task.created",
            "timestamp": "2026-01-13T12:00:00Z",
            "user_id": "user123"
        }

        assert validate_event(event) is False

    def test_validate_event_missing_event_type(self):
        """Test event missing event_type fails validation"""
        event = {
            "event_id": str(uuid4()),
            "timestamp": "2026-01-13T12:00:00Z",
            "user_id": "user123"
        }

        assert validate_event(event) is False

    def test_validate_event_missing_timestamp(self):
        """Test event missing timestamp fails validation"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "task.created",
            "user_id": "user123"
        }

        assert validate_event(event) is False

    def test_validate_event_missing_user_id(self):
        """Test event missing user_id fails validation"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "task.created",
            "timestamp": "2026-01-13T12:00:00Z"
        }

        assert validate_event(event) is False

    def test_validate_event_unknown_type_warns_but_passes(self):
        """Test unknown event_type warns but passes validation"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "unknown.type",
            "timestamp": "2026-01-13T12:00:00Z",
            "user_id": "user123"
        }

        # Should still pass - we want to log all events
        assert validate_event(event) is True


class TestParseEventToAuditLog:
    """Test event parsing logic"""

    def test_parse_task_created_event(self):
        """Test parsing task.created event"""
        event_id = str(uuid4())
        event = {
            "event_id": event_id,
            "event_type": "task.created",
            "schema_version": "1.0.0",
            "timestamp": "2026-01-13T12:00:00Z",
            "user_id": "user123",
            "task_id": 42,
            "task_data": {
                "id": 42,
                "user_id": "user123",
                "title": "Buy groceries",
                "completed": False
            }
        }

        result = parse_event_to_audit_log(event)

        assert result is not None
        assert isinstance(result["event_id"], UUID)
        assert str(result["event_id"]) == event_id
        assert result["operation_type"] == "task.created"
        assert result["user_id"] == "user123"
        assert result["task_id"] == 42
        assert isinstance(result["timestamp"], datetime)
        assert result["event_payload"] == event
        assert result["system_generated"] is False

    def test_parse_task_updated_event(self):
        """Test parsing task.updated event"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "task.updated",
            "timestamp": "2026-01-13T13:00:00Z",
            "user_id": "user456",
            "task_id": 99,
            "task_data": {"title": "Updated task"}
        }

        result = parse_event_to_audit_log(event)

        assert result is not None
        assert result["operation_type"] == "task.updated"
        assert result["user_id"] == "user456"
        assert result["task_id"] == 99

    def test_parse_task_deleted_event(self):
        """Test parsing task.deleted event"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "task.deleted",
            "timestamp": "2026-01-13T14:00:00Z",
            "user_id": "user789",
            "task_id": 77,
            "task_data": {}
        }

        result = parse_event_to_audit_log(event)

        assert result is not None
        assert result["operation_type"] == "task.deleted"
        assert result["task_id"] == 77

    def test_parse_event_system_generated_from_source(self):
        """Test system_generated=True when source is recurring-task-service"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "task.created",
            "timestamp": "2026-01-13T12:00:00Z",
            "user_id": "user123",
            "task_id": 42,
            "source": "recurring-task-service",
            "task_data": {"title": "Auto-created task"}
        }

        result = parse_event_to_audit_log(event)

        assert result is not None
        assert result["system_generated"] is True

    def test_parse_event_system_generated_from_parent_task_id(self):
        """Test system_generated=True when task has parent_task_id"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "task.created",
            "timestamp": "2026-01-13T12:00:00Z",
            "user_id": "user123",
            "task_id": 42,
            "task_data": {
                "title": "Recurring instance",
                "parent_task_id": 10
            }
        }

        result = parse_event_to_audit_log(event)

        assert result is not None
        assert result["system_generated"] is True

    def test_parse_event_missing_event_id(self):
        """Test parsing fails gracefully for missing event_id"""
        event = {
            "event_type": "task.created",
            "timestamp": "2026-01-13T12:00:00Z",
            "user_id": "user123"
        }

        result = parse_event_to_audit_log(event)

        assert result is None

    def test_parse_event_missing_event_type(self):
        """Test parsing fails gracefully for missing event_type"""
        event = {
            "event_id": str(uuid4()),
            "timestamp": "2026-01-13T12:00:00Z",
            "user_id": "user123"
        }

        result = parse_event_to_audit_log(event)

        assert result is None

    def test_parse_event_missing_timestamp(self):
        """Test parsing fails gracefully for missing timestamp"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "task.created",
            "user_id": "user123"
        }

        result = parse_event_to_audit_log(event)

        assert result is None

    def test_parse_event_missing_user_id(self):
        """Test parsing fails gracefully for missing user_id"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "task.created",
            "timestamp": "2026-01-13T12:00:00Z"
        }

        result = parse_event_to_audit_log(event)

        assert result is None

    def test_parse_event_invalid_event_id_format(self):
        """Test parsing fails for invalid UUID format"""
        event = {
            "event_id": "not-a-valid-uuid",
            "event_type": "task.created",
            "timestamp": "2026-01-13T12:00:00Z",
            "user_id": "user123"
        }

        result = parse_event_to_audit_log(event)

        assert result is None

    def test_parse_event_invalid_timestamp_format(self):
        """Test parsing fails for invalid timestamp format"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "task.created",
            "timestamp": "not-a-valid-timestamp",
            "user_id": "user123"
        }

        result = parse_event_to_audit_log(event)

        assert result is None

    def test_parse_event_with_task_id_none(self):
        """Test parsing succeeds with task_id=None"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "task.created",
            "timestamp": "2026-01-13T12:00:00Z",
            "user_id": "user123",
            "task_id": None,
            "task_data": {}
        }

        result = parse_event_to_audit_log(event)

        assert result is not None
        assert result["task_id"] is None

    def test_parse_event_timestamp_with_microseconds(self):
        """Test parsing timestamp with microseconds"""
        event = {
            "event_id": str(uuid4()),
            "event_type": "task.created",
            "timestamp": "2026-01-13T12:00:00.123456Z",
            "user_id": "user123",
            "task_id": 42,
            "task_data": {}
        }

        result = parse_event_to_audit_log(event)

        assert result is not None
        assert isinstance(result["timestamp"], datetime)
        assert result["timestamp"].microsecond == 123456
