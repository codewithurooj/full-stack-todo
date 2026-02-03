"""
Audit Logger
Inserts audit log entries into the database
"""
from typing import Dict, Any, List
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError
import logging

from src.models import AuditLog

logger = logging.getLogger(__name__)


async def insert_audit_log(
    audit_log_data: Dict[str, Any],
    session: Session
) -> bool:
    """
    Insert a single audit log entry into the database

    Args:
        audit_log_data: Parsed audit log data
        session: Database session

    Returns:
        True if inserted successfully, False if duplicate (idempotency)

    Raises:
        Exception: For non-idempotency database errors
    """
    try:
        # Create AuditLog model
        audit_log = AuditLog(**audit_log_data)

        # Insert into database
        session.add(audit_log)
        session.commit()

        logger.info(
            f"Inserted audit log: event_id={audit_log.event_id}, "
            f"type={audit_log.operation_type}, user={audit_log.user_id}, "
            f"task={audit_log.task_id}"
        )

        return True

    except IntegrityError as e:
        # Duplicate event_id detected (idempotency working correctly)
        session.rollback()
        logger.info(
            f"Duplicate audit log detected for event_id={audit_log_data.get('event_id')}, "
            f"skipping (idempotency working)"
        )
        return False

    except Exception as e:
        session.rollback()
        logger.error(
            f"Failed to insert audit log for event_id={audit_log_data.get('event_id')}: {e}",
            exc_info=True
        )
        raise


async def batch_insert_audit_logs(
    audit_logs_data: List[Dict[str, Any]],
    session: Session
) -> int:
    """
    Insert multiple audit log entries in a batch

    Args:
        audit_logs_data: List of parsed audit log data
        session: Database session

    Returns:
        Number of successfully inserted logs

    Note:
        This function handles duplicates gracefully - if one insert fails
        due to duplicate event_id, it continues with the remaining inserts.
    """
    inserted_count = 0
    skipped_count = 0

    for audit_log_data in audit_logs_data:
        try:
            success = await insert_audit_log(audit_log_data, session)
            if success:
                inserted_count += 1
            else:
                skipped_count += 1

        except Exception as e:
            logger.error(
                f"Error inserting audit log in batch: {e}",
                exc_info=True
            )
            # Continue with remaining logs

    logger.info(
        f"Batch insert complete: inserted={inserted_count}, "
        f"skipped={skipped_count}, total={len(audit_logs_data)}"
    )

    return inserted_count
