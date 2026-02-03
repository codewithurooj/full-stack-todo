"""
Audit Consumer
Consumes ALL task events from Kafka and logs them to audit_logs table
"""
import json
import asyncio
import logging
import time
from typing import Dict, Any, List
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from sqlmodel import Session, create_engine

from src.parser import parse_event_to_audit_log, validate_event
from src.audit_logger import batch_insert_audit_logs
from src.config import settings

logger = logging.getLogger(__name__)


class AuditConsumer:
    """Consumes all task events and logs them to audit_logs table"""

    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topic: str,
        database_url: str,
        batch_size: int = 100,
        batch_timeout: float = 10.0
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topic = topic
        self.database_url = database_url
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.consumer = None
        self.running = False

        # Initialize database engine
        self.engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True
        )

        # Batch processing state
        self.pending_audit_logs: List[Dict[str, Any]] = []
        self.last_commit_time = time.time()

        # Metrics
        self.events_consumed = 0
        self.logs_inserted = 0
        self.errors = 0

    async def start(self):
        """Start consuming messages"""
        logger.info(f"Initializing Kafka consumer for topic: {self.topic}")

        # Configure SASL authentication if credentials provided
        sasl_mechanism = None
        sasl_plain_username = None
        sasl_plain_password = None
        security_protocol = settings.KAFKA_SECURITY_PROTOCOL

        if settings.KAFKA_SASL_USERNAME and settings.KAFKA_SASL_PASSWORD:
            sasl_mechanism = "SCRAM-SHA-256"
            sasl_plain_username = settings.KAFKA_SASL_USERNAME
            sasl_plain_password = settings.KAFKA_SASL_PASSWORD
            if security_protocol == "PLAINTEXT":
                security_protocol = "SASL_SSL"

        # Create consumer
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=False,  # Manual batch commit
            max_poll_interval_ms=300000,  # 5 minutes
            session_timeout_ms=60000,  # 1 minute
            security_protocol=security_protocol,
            sasl_mechanism=sasl_mechanism,
            sasl_plain_username=sasl_plain_username,
            sasl_plain_password=sasl_plain_password,
        )

        await self.consumer.start()
        self.running = True
        self.last_commit_time = time.time()
        logger.info("Consumer started, waiting for messages...")

        # Consume messages
        try:
            async for message in self.consumer:
                if not self.running:
                    break

                try:
                    event = message.value
                    event_type = event.get("event_type")
                    event_id = event.get("event_id")

                    logger.debug(
                        f"Received event: type={event_type}, event_id={event_id}, "
                        f"partition={message.partition}, offset={message.offset}"
                    )

                    # Process ALL event types (no filtering for audit service)
                    await self.process_event(event)

                    self.events_consumed += 1

                    # Check if batch should be committed
                    should_commit = await self.should_commit_batch()

                    if should_commit:
                        await self.commit_batch()

                except Exception as e:
                    logger.error(
                        f"Error processing message at offset {message.offset}: {e}",
                        exc_info=True
                    )
                    self.errors += 1
                    # Continue processing (don't commit this offset yet)

                # Log metrics every 100 events
                if self.events_consumed > 0 and self.events_consumed % 100 == 0:
                    logger.info(
                        f"Metrics: consumed={self.events_consumed}, "
                        f"inserted={self.logs_inserted}, errors={self.errors}"
                    )

        except KafkaError as e:
            logger.error(f"Kafka error: {e}", exc_info=True)
            raise

    async def stop(self):
        """Stop consuming messages"""
        self.running = False

        # Commit any pending batch
        if self.pending_audit_logs:
            logger.info(f"Committing final batch of {len(self.pending_audit_logs)} events...")
            await self.commit_batch()

        if self.consumer:
            await self.consumer.stop()
            logger.info("Consumer closed")

        logger.info(
            f"Final metrics: consumed={self.events_consumed}, "
            f"inserted={self.logs_inserted}, errors={self.errors}"
        )

    async def process_event(self, event: Dict[str, Any]):
        """
        Process a single event by parsing and adding to batch

        Args:
            event: Kafka event dictionary
        """
        # Validate event
        if not validate_event(event):
            logger.warning(f"Invalid event structure, skipping: {event.get('event_id')}")
            return

        # Parse event to audit log format
        audit_log_data = parse_event_to_audit_log(event)

        if not audit_log_data:
            logger.warning(f"Failed to parse event: {event.get('event_id')}")
            return

        # Add to pending batch
        self.pending_audit_logs.append(audit_log_data)

        logger.debug(
            f"Added to batch: event_id={audit_log_data.get('event_id')}, "
            f"batch_size={len(self.pending_audit_logs)}/{self.batch_size}"
        )

    async def should_commit_batch(self) -> bool:
        """
        Check if batch should be committed based on size or timeout

        Returns:
            True if batch should be committed, False otherwise
        """
        # Check batch size
        if len(self.pending_audit_logs) >= self.batch_size:
            logger.debug(f"Batch size limit reached: {len(self.pending_audit_logs)}")
            return True

        # Check timeout
        time_since_last_commit = time.time() - self.last_commit_time
        if time_since_last_commit >= self.batch_timeout:
            if self.pending_audit_logs:
                logger.debug(
                    f"Batch timeout reached: {time_since_last_commit:.1f}s, "
                    f"committing {len(self.pending_audit_logs)} events"
                )
                return True

        return False

    async def commit_batch(self):
        """
        Commit the current batch to database and Kafka offset
        """
        if not self.pending_audit_logs:
            logger.debug("No pending audit logs to commit")
            return

        batch_size = len(self.pending_audit_logs)
        logger.info(f"Committing batch of {batch_size} audit logs...")

        try:
            # Insert batch into database
            with Session(self.engine) as session:
                inserted_count = await batch_insert_audit_logs(
                    self.pending_audit_logs,
                    session
                )

                self.logs_inserted += inserted_count

            # Commit Kafka offset (only after successful database insert)
            await self.consumer.commit()

            logger.info(
                f"Batch committed successfully: {inserted_count}/{batch_size} inserted, "
                f"offset committed"
            )

            # Clear batch
            self.pending_audit_logs = []
            self.last_commit_time = time.time()

        except Exception as e:
            logger.error(f"Failed to commit batch: {e}", exc_info=True)
            # Don't clear pending_audit_logs - will retry in next batch
            raise
