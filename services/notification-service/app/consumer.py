"""
Kafka consumer for reminders topic
Consumes reminder events and schedules Web Push notifications
"""
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from pywebpush import webpush, WebPushException
from sqlmodel import Session, create_engine, select
from app.config import settings
from app.models import NotificationLog, PushSubscription, UserNotificationStats
from app.utils import (
    NotificationBatcher,
    RateLimiter,
    validate_reminder_event,
    parse_iso_datetime,
    calculate_delay
)

logger = logging.getLogger(__name__)


class NotificationConsumer:
    """Consumes reminder events from Kafka and sends Web Push notifications"""

    def __init__(self, bootstrap_servers: str, group_id: str, topic: str):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topic = topic
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.running = False

        # Initialize database engine
        if settings.DATABASE_URL:
            self.engine = create_engine(settings.DATABASE_URL)
        else:
            self.engine = None
            logger.warning("DATABASE_URL not set, database operations will be skipped")

        # Initialize notification utilities
        self.batcher = NotificationBatcher(window_seconds=settings.BATCH_WINDOW_SECONDS)
        self.rate_limiter = RateLimiter(
            max_per_window=settings.RATE_LIMIT_PER_USER,
            window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS
        )

        # Track scheduled notifications
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}

    async def start(self):
        """Start consuming messages"""
        logger.info(f"Initializing Kafka consumer for topic: {self.topic}")

        # Create consumer
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            max_poll_interval_ms=300000,  # 5 minutes
            session_timeout_ms=60000      # 1 minute
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
                    logger.info(f"Received reminder event: {event.get('reminder_id')}")

                    # Process event
                    await self.process_event(event)

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    # Continue processing other messages

        except KafkaError as e:
            logger.error(f"Kafka error: {e}", exc_info=True)
            raise

    async def stop(self):
        """Stop consuming messages"""
        self.running = False

        # Cancel all scheduled notifications
        logger.info(f"Cancelling {len(self.scheduled_tasks)} scheduled notifications...")
        for task in self.scheduled_tasks.values():
            task.cancel()

        if self.consumer:
            await self.consumer.stop()
            logger.info("Consumer closed")

    async def process_event(self, event: Dict[str, Any]):
        """
        Process a reminder event by scheduling a notification

        Args:
            event: Reminder event data from Kafka
        """
        # Validate event schema
        if not validate_reminder_event(event):
            logger.error(f"Invalid event schema: {event}")
            return

        reminder_id = event['reminder_id']
        task_id = event['task_id']
        user_id = event['user_id']
        title = event['title']
        remind_at_str = event['remind_at']
        due_date_str = event.get('due_date')

        # Parse remind_at datetime
        remind_at = parse_iso_datetime(remind_at_str)
        if not remind_at:
            logger.error(f"Failed to parse remind_at: {remind_at_str}")
            return

        # Calculate delay
        delay = calculate_delay(remind_at)

        logger.info(
            f"Scheduling notification for reminder {reminder_id} "
            f"(task {task_id}, user {user_id}) in {delay:.1f} seconds"
        )

        # Schedule notification
        task = asyncio.create_task(
            self._schedule_notification(
                reminder_id=reminder_id,
                task_id=task_id,
                user_id=user_id,
                title=title,
                remind_at=remind_at,
                due_date=due_date_str,
                delay=delay
            )
        )

        self.scheduled_tasks[reminder_id] = task

    async def _schedule_notification(
        self,
        reminder_id: str,
        task_id: int,
        user_id: int,
        title: str,
        remind_at: datetime,
        due_date: Optional[str],
        delay: float
    ):
        """Schedule and send notification after delay"""
        try:
            # Wait until remind_at time
            if delay > 0:
                logger.debug(f"Waiting {delay:.1f}s for reminder {reminder_id}")
                await asyncio.sleep(delay)

            # Check rate limit
            if not self.rate_limiter.is_allowed(user_id):
                logger.warning(f"Rate limit exceeded for user {user_id}, skipping notification")
                await self._log_notification(
                    reminder_id, task_id, user_id,
                    status='rate_limited',
                    error_message='Rate limit exceeded'
                )
                return

            # Send notification
            await self.send_notification(
                reminder_id=reminder_id,
                task_id=task_id,
                user_id=user_id,
                title=title,
                due_date=due_date
            )

            # Mark task as reminded in database
            await self._mark_task_reminded(task_id)

        except asyncio.CancelledError:
            logger.info(f"Notification {reminder_id} cancelled")
            raise
        except Exception as e:
            logger.error(f"Error sending notification {reminder_id}: {e}", exc_info=True)
            await self._log_notification(
                reminder_id, task_id, user_id,
                status='failed',
                error_message=str(e)
            )
        finally:
            # Clean up scheduled task
            if reminder_id in self.scheduled_tasks:
                del self.scheduled_tasks[reminder_id]

    async def send_notification(
        self,
        reminder_id: str,
        task_id: int,
        user_id: int,
        title: str,
        due_date: Optional[str]
    ):
        """Send Web Push notification to user"""
        logger.info(f"Sending notification for reminder {reminder_id} to user {user_id}")

        # Get user's push subscriptions
        subscriptions = await self._get_user_subscriptions(user_id)

        if not subscriptions:
            logger.warning(f"No push subscriptions found for user {user_id}")
            await self._log_notification(
                reminder_id, task_id, user_id,
                status='failed',
                error_message='No push subscriptions'
            )
            return

        # Prepare notification payload
        payload = json.dumps({
            'title': 'Task Reminder',
            'body': title,
            'data': {
                'task_id': task_id,
                'reminder_id': reminder_id,
                'due_date': due_date
            }
        })

        # Send to all subscriptions
        success_count = 0
        for subscription in subscriptions:
            try:
                webpush(
                    subscription_info={
                        'endpoint': subscription.endpoint,
                        'keys': {
                            'p256dh': subscription.p256dh,
                            'auth': subscription.auth
                        }
                    },
                    data=payload,
                    vapid_private_key=settings.VAPID_PRIVATE_KEY,
                    vapid_claims={'sub': settings.VAPID_CLAIMS_EMAIL}
                )
                success_count += 1
                logger.info(f"Notification sent to subscription {subscription.id}")

            except WebPushException as e:
                logger.error(f"Failed to send to subscription {subscription.id}: {e}")

                # If subscription is invalid, mark as inactive
                if e.response and e.response.status_code in [404, 410]:
                    await self._deactivate_subscription(subscription.id)

        if success_count > 0:
            await self._log_notification(
                reminder_id, task_id, user_id,
                status='sent'
            )
            logger.info(f"Notification sent successfully to {success_count} subscriptions")
        else:
            await self._log_notification(
                reminder_id, task_id, user_id,
                status='failed',
                error_message='All subscriptions failed'
            )

    async def _get_user_subscriptions(self, user_id: int) -> list:
        """Get active push subscriptions for user"""
        if not self.engine:
            return []

        with Session(self.engine) as session:
            statement = select(PushSubscription).where(
                PushSubscription.user_id == user_id,
                PushSubscription.active == True
            )
            subscriptions = session.exec(statement).all()
            return list(subscriptions)

    async def _deactivate_subscription(self, subscription_id: int):
        """Mark push subscription as inactive"""
        if not self.engine:
            return

        with Session(self.engine) as session:
            statement = select(PushSubscription).where(
                PushSubscription.id == subscription_id
            )
            subscription = session.exec(statement).first()
            if subscription:
                subscription.active = False
                session.add(subscription)
                session.commit()
                logger.info(f"Deactivated subscription {subscription_id}")

    async def _mark_task_reminded(self, task_id: int):
        """Mark task as reminded in database"""
        if not self.engine:
            return

        try:
            with Session(self.engine) as session:
                # Execute raw SQL since we don't have the Task model here
                session.exec(
                    f"UPDATE tasks SET reminded = true WHERE id = {task_id}"
                )
                session.commit()
                logger.debug(f"Marked task {task_id} as reminded")
        except Exception as e:
            logger.error(f"Failed to mark task {task_id} as reminded: {e}")

    async def _log_notification(
        self,
        reminder_id: str,
        task_id: int,
        user_id: int,
        status: str,
        error_message: Optional[str] = None
    ):
        """Log notification attempt to database"""
        if not self.engine:
            return

        try:
            with Session(self.engine) as session:
                log = NotificationLog(
                    reminder_id=reminder_id,
                    task_id=task_id,
                    user_id=user_id,
                    status=status,
                    error_message=error_message
                )
                session.add(log)
                session.commit()
                logger.debug(f"Logged notification: {reminder_id} - {status}")
        except Exception as e:
            logger.error(f"Failed to log notification: {e}")
