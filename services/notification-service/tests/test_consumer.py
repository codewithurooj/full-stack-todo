"""
Tests for notification consumer
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from app.consumer import NotificationConsumer
from tests.fixtures import (
    sample_reminder_event,
    past_reminder_event,
    future_reminder_event,
    invalid_reminder_event,
    sample_push_subscription
)


@pytest.fixture
def consumer():
    """Create consumer instance for testing"""
    with patch('app.consumer.create_engine'):
        consumer = NotificationConsumer(
            bootstrap_servers="localhost:9092",
            group_id="test-group",
            topic="test-topic"
        )
        consumer.engine = None  # Disable database for most tests
        return consumer


@pytest.mark.asyncio
async def test_process_valid_event(consumer, sample_reminder_event):
    """Test processing valid reminder event"""
    # Mock scheduling method
    consumer._schedule_notification = AsyncMock()

    # Process event
    await consumer.process_event(sample_reminder_event)

    # Verify notification was scheduled
    assert len(consumer.scheduled_tasks) == 1
    assert sample_reminder_event['reminder_id'] in consumer.scheduled_tasks


@pytest.mark.asyncio
async def test_process_invalid_event(consumer, invalid_reminder_event):
    """Test processing invalid event is rejected"""
    # Mock scheduling method
    consumer._schedule_notification = AsyncMock()

    # Process event
    await consumer.process_event(invalid_reminder_event)

    # Verify notification was NOT scheduled
    assert len(consumer.scheduled_tasks) == 0
    consumer._schedule_notification.assert_not_called()


@pytest.mark.asyncio
async def test_rate_limiting(consumer, sample_reminder_event):
    """Test rate limiting prevents excessive notifications"""
    user_id = sample_reminder_event['user_id']

    # Exhaust rate limit
    for _ in range(consumer.rate_limiter.max_per_window):
        assert consumer.rate_limiter.is_allowed(user_id) is True

    # Next notification should be blocked
    assert consumer.rate_limiter.is_allowed(user_id) is False


@pytest.mark.asyncio
async def test_send_notification_success(consumer, sample_reminder_event, sample_push_subscription):
    """Test sending notification successfully"""
    # Mock database and webpush
    consumer._get_user_subscriptions = AsyncMock(return_value=[
        MagicMock(**sample_push_subscription)
    ])
    consumer._log_notification = AsyncMock()

    with patch('app.consumer.webpush') as mock_webpush:
        # Send notification
        await consumer.send_notification(
            reminder_id=sample_reminder_event['reminder_id'],
            task_id=sample_reminder_event['task_id'],
            user_id=sample_reminder_event['user_id'],
            title=sample_reminder_event['title'],
            due_date=sample_reminder_event['due_date']
        )

        # Verify webpush was called
        mock_webpush.assert_called_once()

        # Verify success was logged
        consumer._log_notification.assert_called_once()
        call_args = consumer._log_notification.call_args[1]
        assert call_args['status'] == 'sent'


@pytest.mark.asyncio
async def test_send_notification_no_subscriptions(consumer, sample_reminder_event):
    """Test handling user with no push subscriptions"""
    # Mock database to return no subscriptions
    consumer._get_user_subscriptions = AsyncMock(return_value=[])
    consumer._log_notification = AsyncMock()

    # Send notification
    await consumer.send_notification(
        reminder_id=sample_reminder_event['reminder_id'],
        task_id=sample_reminder_event['task_id'],
        user_id=sample_reminder_event['user_id'],
        title=sample_reminder_event['title'],
        due_date=sample_reminder_event['due_date']
    )

    # Verify failure was logged
    consumer._log_notification.assert_called_once()
    call_args = consumer._log_notification.call_args[1]
    assert call_args['status'] == 'failed'
    assert 'No push subscriptions' in call_args['error_message']


@pytest.mark.asyncio
async def test_schedule_notification_with_delay(consumer, future_reminder_event):
    """Test notification is scheduled with correct delay"""
    # Mock send methods
    consumer.send_notification = AsyncMock()
    consumer._mark_task_reminded = AsyncMock()
    consumer._log_notification = AsyncMock()

    # Process event (this schedules the notification)
    await consumer.process_event(future_reminder_event)

    # Wait a short time (not the full delay)
    await asyncio.sleep(0.1)

    # Verify notification hasn't been sent yet
    consumer.send_notification.assert_not_called()

    # Clean up
    for task in consumer.scheduled_tasks.values():
        task.cancel()


@pytest.mark.asyncio
async def test_schedule_notification_immediate(consumer, past_reminder_event):
    """Test past reminder triggers immediately"""
    # Mock send methods
    consumer.send_notification = AsyncMock()
    consumer._mark_task_reminded = AsyncMock()
    consumer._log_notification = AsyncMock()

    # Process event
    await consumer.process_event(past_reminder_event)

    # Wait for task to complete
    await asyncio.sleep(0.2)

    # Verify notification was sent
    consumer.send_notification.assert_called_once()


@pytest.mark.asyncio
async def test_graceful_shutdown(consumer, future_reminder_event):
    """Test scheduled notifications are cancelled on shutdown"""
    # Process event to schedule notification
    await consumer.process_event(future_reminder_event)

    # Verify task is scheduled
    assert len(consumer.scheduled_tasks) == 1

    # Stop consumer
    await consumer.stop()

    # Verify all tasks were cancelled
    for task in consumer.scheduled_tasks.values():
        assert task.cancelled() or task.done()
