"""
Kafka producer service with lifecycle management
Feature 011: Event-Driven Architecture with Kafka

DEPRECATION WARNING (Feature 012):
This module is deprecated in favor of Dapr pub/sub via dapr_event_publisher.py.
When DAPR_ENABLED=true, the application will use Dapr for event publishing instead.
This module is kept as a fallback for environments where Dapr is not available.

To migrate:
1. Set DAPR_ENABLED=true in your environment
2. Ensure Dapr sidecar is running alongside your application
3. Use dapr_event_publisher.publish_task_event() instead of kafka_producer.publish_task_event()

This module will be removed in a future version once Dapr adoption is complete.
"""
import json
import logging
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from app.config import settings
from app.schemas.events import TaskEventSchema, ReminderEventSchema

logger = logging.getLogger(__name__)


class KafkaProducerService:
    """Async Kafka producer with startup/shutdown lifecycle"""

    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.is_started = False
        self.publish_count = 0
        self.error_count = 0
        self.total_latency = 0.0

    async def start(self):
        """Start the Kafka producer"""
        if self.is_started:
            logger.warning("Kafka producer already started")
            return

        try:
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

            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                compression_type="gzip",
                acks="all",  # Wait for all replicas to acknowledge
                retries=3,  # Retry failed sends up to 3 times
                max_in_flight_requests_per_connection=5,
                enable_idempotence=True,  # Ensure exactly-once semantics
                security_protocol=security_protocol,
                sasl_mechanism=sasl_mechanism,
                sasl_plain_username=sasl_plain_username,
                sasl_plain_password=sasl_plain_password,
            )

            await self.producer.start()
            self.is_started = True
            logger.info(f"Kafka producer started: {settings.KAFKA_BOOTSTRAP_SERVERS}")

        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")
            raise

    async def stop(self):
        """Stop the Kafka producer"""
        if not self.is_started:
            return

        try:
            if self.producer:
                await self.producer.stop()
            self.is_started = False
            logger.info("Kafka producer stopped")

        except Exception as e:
            logger.error(f"Error stopping Kafka producer: {e}")

    async def publish_task_event(
        self,
        event_type: str,
        user_id: str,
        task_id: int,
        task_data: dict,
        event_id: Optional[UUID] = None,
    ) -> Optional[UUID]:
        """
        Publish a task event to the task-events topic

        Args:
            event_type: Type of event (task.created, task.updated, task.deleted, task.completed)
            user_id: User who owns the task
            task_id: Task identifier
            task_data: Full task object
            event_id: Optional event ID for idempotency (generated if not provided)

        Returns:
            UUID of the published event, or None if publishing failed
        """
        if not self.is_started:
            logger.error("Kafka producer not started, cannot publish event")
            return None

        start_time = datetime.utcnow()

        try:
            # Generate event ID if not provided
            if event_id is None:
                event_id = uuid4()

            # Create event schema
            event = TaskEventSchema(
                event_id=event_id,
                event_type=event_type,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                task_id=task_id,
                task_data=task_data,
            )

            # Validate event
            event_dict = event.model_dump(mode="json")

            # Publish to Kafka with user_id as partition key for ordering
            await self.producer.send(
                topic="task-events",
                key=user_id,  # Partition by user_id for per-user ordering
                value=event_dict,
            )

            # Update metrics
            self.publish_count += 1
            latency = (datetime.utcnow() - start_time).total_seconds()
            self.total_latency += latency

            logger.info(
                f"Published {event_type} event: task_id={task_id}, user_id={user_id}, "
                f"event_id={event_id}, latency={latency:.3f}s"
            )

            return event_id

        except KafkaError as e:
            self.error_count += 1
            logger.error(f"Kafka error publishing event: {e}")
            # Fallback: log event for manual replay
            logger.error(
                f"FALLBACK LOG - Event not published: {event_type}, task_id={task_id}, "
                f"user_id={user_id}, task_data={task_data}"
            )
            return None

        except Exception as e:
            self.error_count += 1
            logger.error(f"Error publishing event: {e}")
            return None

    async def publish_reminder_event(
        self,
        task_id: int,
        user_id: str,
        title: str,
        remind_at: datetime,
        due_date: Optional[datetime] = None,
        event_id: Optional[UUID] = None,
    ) -> Optional[UUID]:
        """
        Publish a reminder event to the reminders topic

        Args:
            task_id: Task to remind about
            user_id: User to notify
            title: Task title for notification
            remind_at: When to send notification
            due_date: Task due date for context
            event_id: Optional event ID for idempotency

        Returns:
            UUID of the published event, or None if publishing failed
        """
        if not self.is_started:
            logger.error("Kafka producer not started, cannot publish reminder")
            return None

        start_time = datetime.utcnow()

        try:
            # Generate event ID if not provided
            if event_id is None:
                event_id = uuid4()

            # Create reminder ID for idempotency
            reminder_id = f"reminder-{task_id}-{remind_at.isoformat()}"

            # Create event schema
            event = ReminderEventSchema(
                event_id=event_id,
                timestamp=datetime.utcnow(),
                reminder_id=reminder_id,
                task_id=task_id,
                user_id=user_id,
                title=title,
                remind_at=remind_at,
                due_date=due_date,
            )

            # Validate event
            event_dict = event.model_dump(mode="json")

            # Publish to Kafka with user_id as partition key
            await self.producer.send(
                topic="reminders",
                key=user_id,
                value=event_dict,
            )

            # Update metrics
            self.publish_count += 1
            latency = (datetime.utcnow() - start_time).total_seconds()
            self.total_latency += latency

            logger.info(
                f"Published reminder event: reminder_id={reminder_id}, task_id={task_id}, "
                f"user_id={user_id}, event_id={event_id}, latency={latency:.3f}s"
            )

            return event_id

        except KafkaError as e:
            self.error_count += 1
            logger.error(f"Kafka error publishing reminder: {e}")
            logger.error(
                f"FALLBACK LOG - Reminder not published: task_id={task_id}, "
                f"user_id={user_id}, remind_at={remind_at}"
            )
            return None

        except Exception as e:
            self.error_count += 1
            logger.error(f"Error publishing reminder: {e}")
            return None

    def get_metrics(self) -> dict:
        """Get producer metrics"""
        avg_latency = self.total_latency / self.publish_count if self.publish_count > 0 else 0.0

        return {
            "is_started": self.is_started,
            "publish_count": self.publish_count,
            "error_count": self.error_count,
            "average_latency_seconds": round(avg_latency, 3),
        }


# Global producer instance
kafka_producer = KafkaProducerService()
