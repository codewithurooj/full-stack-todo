"""
Test Idempotency
Tests duplicate event handling via database unique constraint
"""
import pytest
from uuid import uuid4
from datetime import datetime
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.exc import IntegrityError

from src.models import AuditLog
from src.audit_logger import insert_audit_log, batch_insert_audit_logs


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    SQLModel.metadata.create_all(engine)
    return engine


class TestIdempotency:
    """Test idempotency via unique constraint on event_id"""

    @pytest.mark.asyncio
    async def test_insert_duplicate_event_id_prevented(self, in_memory_db):
        """Test duplicate event_id is prevented by unique constraint"""
        event_id = uuid4()

        audit_log_data_1 = {
            "event_id": event_id,
            "timestamp": datetime.utcnow(),
            "user_id": "user123",
            "task_id": 42,
            "operation_type": "task.created",
            "event_payload": {"test": "data"},
            "system_generated": False
        }

        audit_log_data_2 = {
            "event_id": event_id,  # Same event_id
            "timestamp": datetime.utcnow(),
            "user_id": "user456",  # Different user
            "task_id": 99,  # Different task
            "operation_type": "task.updated",
            "event_payload": {"test": "different data"},
            "system_generated": True
        }

        with Session(in_memory_db) as session:
            # First insert should succeed
            result1 = await insert_audit_log(audit_log_data_1, session)
            assert result1 is True

            # Second insert with same event_id should fail gracefully
            result2 = await insert_audit_log(audit_log_data_2, session)
            assert result2 is False

            # Verify only one entry exists
            audit_logs = session.query(AuditLog).all()
            assert len(audit_logs) == 1
            assert audit_logs[0].event_id == event_id
            assert audit_logs[0].user_id == "user123"  # First insert data

    @pytest.mark.asyncio
    async def test_insert_different_event_ids_succeed(self, in_memory_db):
        """Test different event_ids can be inserted"""
        audit_log_data_1 = {
            "event_id": uuid4(),
            "timestamp": datetime.utcnow(),
            "user_id": "user123",
            "task_id": 42,
            "operation_type": "task.created",
            "event_payload": {},
            "system_generated": False
        }

        audit_log_data_2 = {
            "event_id": uuid4(),  # Different event_id
            "timestamp": datetime.utcnow(),
            "user_id": "user123",
            "task_id": 42,
            "operation_type": "task.updated",
            "event_payload": {},
            "system_generated": False
        }

        with Session(in_memory_db) as session:
            result1 = await insert_audit_log(audit_log_data_1, session)
            result2 = await insert_audit_log(audit_log_data_2, session)

            assert result1 is True
            assert result2 is True

            # Verify both entries exist
            audit_logs = session.query(AuditLog).all()
            assert len(audit_logs) == 2

    @pytest.mark.asyncio
    async def test_batch_insert_with_duplicates(self, in_memory_db):
        """Test batch insert handles duplicates gracefully"""
        event_id_1 = uuid4()
        event_id_2 = uuid4()
        event_id_3 = uuid4()

        # First batch
        batch_1 = [
            {
                "event_id": event_id_1,
                "timestamp": datetime.utcnow(),
                "user_id": "user123",
                "task_id": 1,
                "operation_type": "task.created",
                "event_payload": {},
                "system_generated": False
            },
            {
                "event_id": event_id_2,
                "timestamp": datetime.utcnow(),
                "user_id": "user123",
                "task_id": 2,
                "operation_type": "task.created",
                "event_payload": {},
                "system_generated": False
            }
        ]

        # Second batch with one duplicate and one new
        batch_2 = [
            {
                "event_id": event_id_2,  # Duplicate
                "timestamp": datetime.utcnow(),
                "user_id": "user456",
                "task_id": 99,
                "operation_type": "task.updated",
                "event_payload": {},
                "system_generated": False
            },
            {
                "event_id": event_id_3,  # New
                "timestamp": datetime.utcnow(),
                "user_id": "user123",
                "task_id": 3,
                "operation_type": "task.created",
                "event_payload": {},
                "system_generated": False
            }
        ]

        with Session(in_memory_db) as session:
            # Insert first batch
            inserted_1 = await batch_insert_audit_logs(batch_1, session)
            assert inserted_1 == 2

            # Insert second batch (1 duplicate, 1 new)
            inserted_2 = await batch_insert_audit_logs(batch_2, session)
            assert inserted_2 == 1  # Only the new one inserted

            # Verify total entries
            audit_logs = session.query(AuditLog).all()
            assert len(audit_logs) == 3  # event_id_1, event_id_2, event_id_3

    @pytest.mark.asyncio
    async def test_batch_insert_all_duplicates(self, in_memory_db):
        """Test batch insert where all events are duplicates"""
        event_id = uuid4()

        audit_log_data = {
            "event_id": event_id,
            "timestamp": datetime.utcnow(),
            "user_id": "user123",
            "task_id": 42,
            "operation_type": "task.created",
            "event_payload": {},
            "system_generated": False
        }

        with Session(in_memory_db) as session:
            # Insert once
            result = await insert_audit_log(audit_log_data, session)
            assert result is True

            # Try batch insert with same event_id multiple times
            batch = [audit_log_data] * 5  # Same event 5 times
            inserted = await batch_insert_audit_logs(batch, session)
            assert inserted == 0  # All duplicates, none inserted

            # Verify only one entry
            audit_logs = session.query(AuditLog).all()
            assert len(audit_logs) == 1

    @pytest.mark.asyncio
    async def test_idempotency_with_kafka_replay(self, in_memory_db):
        """Test idempotency when Kafka consumer replays messages"""
        # Simulate Kafka consumer reprocessing same message
        event_id = uuid4()

        audit_log_data = {
            "event_id": event_id,
            "timestamp": datetime.utcnow(),
            "user_id": "user123",
            "task_id": 42,
            "operation_type": "task.created",
            "event_payload": {"message": "original"},
            "system_generated": False
        }

        with Session(in_memory_db) as session:
            # First processing
            result1 = await insert_audit_log(audit_log_data, session)
            assert result1 is True

            # Simulate consumer restart and reprocess (Kafka offset not committed)
            result2 = await insert_audit_log(audit_log_data, session)
            assert result2 is False  # Duplicate detected

            # Third attempt
            result3 = await insert_audit_log(audit_log_data, session)
            assert result3 is False  # Still duplicate

            # Verify only one entry exists
            audit_logs = session.query(AuditLog).all()
            assert len(audit_logs) == 1
            assert audit_logs[0].event_payload["message"] == "original"

    @pytest.mark.asyncio
    async def test_system_generated_flag_preserved_on_duplicate(self, in_memory_db):
        """Test system_generated flag from first insert is preserved"""
        event_id = uuid4()

        # First insert: system_generated=True
        audit_log_data_1 = {
            "event_id": event_id,
            "timestamp": datetime.utcnow(),
            "user_id": "user123",
            "task_id": 42,
            "operation_type": "task.created",
            "event_payload": {},
            "system_generated": True
        }

        # Second insert: system_generated=False (should be rejected)
        audit_log_data_2 = {
            "event_id": event_id,
            "timestamp": datetime.utcnow(),
            "user_id": "user123",
            "task_id": 42,
            "operation_type": "task.created",
            "event_payload": {},
            "system_generated": False
        }

        with Session(in_memory_db) as session:
            result1 = await insert_audit_log(audit_log_data_1, session)
            assert result1 is True

            result2 = await insert_audit_log(audit_log_data_2, session)
            assert result2 is False

            # Verify original system_generated=True is preserved
            audit_log = session.query(AuditLog).filter_by(event_id=event_id).first()
            assert audit_log.system_generated is True
