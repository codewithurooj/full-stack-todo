"""
Recurring Task Consumer
Consumes task.completed events from Kafka and creates next recurring instances
"""
import json
import asyncio
import logging
from typing import Dict, Any
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from sqlmodel import Session, create_engine

from src.recurrence import calculate_next_due_date, should_create_instance
from src.task_creator import create_task_instance, validate_task_data
from src.config import settings

logger = logging.getLogger(__name__)


class RecurringTaskConsumer:
    """Consumes task.completed events and generates next recurring instances"""

    def __init__(self, bootstrap_servers: str, group_id: str, topic: str, database_url: str):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topic = topic
        self.database_url = database_url
        self.consumer = None
        self.running = False

        # Initialize database engine
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL logging
            pool_pre_ping=True
        )

        # Metrics
        self.events_processed = 0
        self.instances_created = 0
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
            enable_auto_commit=False,  # Manual commit after processing
            max_poll_interval_ms=300000,  # 5 minutes
            session_timeout_ms=60000,  # 1 minute
            security_protocol=security_protocol,
            sasl_mechanism=sasl_mechanism,
            sasl_plain_username=sasl_plain_username,
            sasl_plain_password=sasl_plain_password,
        )

        await self.consumer.start()
        self.running = True
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

                    # Filter: Only process task.completed events
                    if event_type == "task.completed":
                        await self.process_completed_task(event)

                    # Commit offset after successful processing
                    await self.consumer.commit()
                    self.events_processed += 1

                except Exception as e:
                    logger.error(
                        f"Error processing message at offset {message.offset}: {e}",
                        exc_info=True
                    )
                    self.errors += 1
                    # Continue processing other messages (don't commit this offset)

                # Log metrics every 100 events
                if self.events_processed > 0 and self.events_processed % 100 == 0:
                    logger.info(
                        f"Metrics: processed={self.events_processed}, "
                        f"created={self.instances_created}, errors={self.errors}"
                    )

        except KafkaError as e:
            logger.error(f"Kafka error: {e}", exc_info=True)
            raise

    async def stop(self):
        """Stop consuming messages"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info("Consumer closed")

        logger.info(
            f"Final metrics: processed={self.events_processed}, "
            f"created={self.instances_created}, errors={self.errors}"
        )

    async def process_completed_task(self, event: Dict[str, Any]):
        """
        Process a task.completed event and create next recurring instance if needed

        Args:
            event: Kafka event containing task completion data
        """
        event_id = event.get("event_id")
        user_id = event.get("user_id")
        task_id = event.get("task_id")
        task_data = event.get("task_data", {})

        logger.info(f"Processing task.completed: event_id={event_id}, task_id={task_id}")

        # Validate task data
        if not validate_task_data(task_data):
            logger.warning(f"Invalid task data in event {event_id}, skipping")
            return

        # Check if task has recurring pattern
        recurring_pattern = task_data.get("recurring_pattern", "none")
        if recurring_pattern == "none":
            logger.debug(f"Task {task_id} has no recurring pattern, skipping")
            return

        # Extract recurring parameters
        recurring_interval = task_data.get("recurring_interval", 1)
        current_due_date = task_data.get("due_date")
        recurring_end_date = task_data.get("recurring_end_date")

        if not current_due_date:
            logger.warning(f"Task {task_id} has no due_date, cannot calculate next instance")
            return

        # Parse dates (they come as ISO 8601 strings)
        from datetime import datetime
        try:
            if isinstance(current_due_date, str):
                current_due_date = datetime.fromisoformat(current_due_date.replace('Z', '+00:00'))
            if recurring_end_date and isinstance(recurring_end_date, str):
                recurring_end_date = datetime.fromisoformat(recurring_end_date.replace('Z', '+00:00'))
        except ValueError as e:
            logger.error(f"Failed to parse dates for task {task_id}: {e}")
            return

        # Calculate next due date
        next_due_date = calculate_next_due_date(
            current_due_date=current_due_date,
            recurring_pattern=recurring_pattern,
            recurring_interval=recurring_interval,
            end_date=recurring_end_date
        )

        if not next_due_date:
            logger.info(
                f"No next due date for task {task_id} "
                f"(pattern={recurring_pattern}, end_date={recurring_end_date})"
            )
            return

        # Check if instance should be created
        if not should_create_instance(next_due_date, recurring_end_date):
            logger.info(f"Skipping instance creation for task {task_id}, date check failed")
            return

        # Create task instance in database with retry logic
        max_retries = settings.MAX_RETRIES
        for attempt in range(max_retries):
            try:
                with Session(self.engine) as session:
                    new_task = await create_task_instance(
                        parent_task_data=task_data,
                        next_due_date=next_due_date,
                        session=session
                    )

                    if new_task:
                        self.instances_created += 1
                        logger.info(
                            f"Successfully created recurring instance {new_task.id} "
                            f"for parent task {task_id}, due_date={next_due_date}"
                        )
                    else:
                        logger.info(
                            f"No instance created for task {task_id} "
                            f"(likely duplicate/idempotency)"
                        )

                    # Success - break retry loop
                    break

            except Exception as e:
                logger.error(
                    f"Attempt {attempt + 1}/{max_retries} failed to create instance "
                    f"for task {task_id}: {e}"
                )

                if attempt < max_retries - 1:
                    # Exponential backoff
                    backoff = settings.RETRY_BACKOFF_BASE * (2 ** attempt)
                    logger.info(f"Retrying in {backoff}s...")
                    await asyncio.sleep(backoff)
                else:
                    # Max retries exceeded
                    logger.error(
                        f"Max retries exceeded for task {task_id}, "
                        f"instance creation failed"
                    )
                    raise  # Re-raise to prevent offset commit
