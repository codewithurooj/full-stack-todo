"""
Prometheus Metrics for Notification Service
Exports metrics for monitoring notification delivery and performance
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging

logger = logging.getLogger(__name__)

# Consumer metrics
reminder_events_consumed_total = Counter(
    'notification_reminder_events_consumed_total',
    'Total number of reminder events consumed'
)

# Notification delivery metrics
notifications_sent_total = Counter(
    'notification_notifications_sent_total',
    'Total number of notifications sent',
    ['status']  # success, failed, rate_limited
)

notification_delivery_duration_seconds = Histogram(
    'notification_delivery_duration_seconds',
    'Time spent delivering notification (Web Push API call)',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Idempotency metrics
duplicate_reminders_skipped_total = Counter(
    'notification_duplicate_reminders_skipped_total',
    'Total number of duplicate reminder_id events skipped'
)

# Batching metrics
notifications_batched_total = Counter(
    'notification_notifications_batched_total',
    'Total number of notifications batched'
)

batches_sent_total = Counter(
    'notification_batches_sent_total',
    'Total number of notification batches sent'
)

batch_size = Histogram(
    'notification_batch_size',
    'Number of notifications per batch',
    buckets=[1, 2, 3, 5, 10, 20, 50]
)

# Rate limiting metrics
rate_limit_hits_total = Counter(
    'notification_rate_limit_hits_total',
    'Total number of rate limit enforcements',
    ['user_id']
)

notifications_queued_total = Counter(
    'notification_notifications_queued_total',
    'Total number of notifications queued due to rate limiting'
)

# Late notification metrics
late_notifications_total = Counter(
    'notification_late_notifications_total',
    'Total number of late notifications (remind_at already passed)'
)

late_notification_delay_seconds = Histogram(
    'notification_late_notification_delay_seconds',
    'Delay for late notifications (how late they were)',
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600]
)

# Consumer lag metrics
consumer_lag = Gauge(
    'notification_consumer_lag',
    'Consumer lag (events behind)',
    ['partition']
)

consumer_offset = Gauge(
    'notification_consumer_offset',
    'Current consumer offset',
    ['partition']
)

# Health metrics
service_health = Gauge(
    'notification_service_health',
    'Service health status (1=healthy, 0=unhealthy)'
)

kafka_connection_status = Gauge(
    'notification_kafka_connection_status',
    'Kafka connection status (1=connected, 0=disconnected)'
)

web_push_api_status = Gauge(
    'notification_web_push_api_status',
    'Web Push API status (1=available, 0=unavailable)'
)

# Subscription metrics
active_subscriptions_total = Gauge(
    'notification_active_subscriptions_total',
    'Total number of active push subscriptions'
)

subscription_failures_total = Counter(
    'notification_subscription_failures_total',
    'Total number of subscription lookup failures'
)


class MetricsCollector:
    """Collects and manages metrics for Notification Service"""

    def __init__(self):
        # Initialize health to healthy
        service_health.set(1)

    def record_reminder_event_consumed(self):
        """Record reminder event consumption"""
        reminder_events_consumed_total.inc()

    def record_notification_sent(self, status: str):
        """Record notification sent with status"""
        notifications_sent_total.labels(status=status).inc()

    def record_notification_delivery_time(self, duration_seconds: float):
        """Record notification delivery duration"""
        notification_delivery_duration_seconds.observe(duration_seconds)

    def record_duplicate_reminder(self):
        """Record duplicate reminder skipped"""
        duplicate_reminders_skipped_total.inc()

    def record_notification_batched(self):
        """Record notification added to batch"""
        notifications_batched_total.inc()

    def record_batch_sent(self, size: int):
        """Record batch sent with size"""
        batches_sent_total.inc()
        batch_size.observe(size)

    def record_rate_limit_hit(self, user_id: str):
        """Record rate limit enforcement"""
        rate_limit_hits_total.labels(user_id=user_id).inc()

    def record_notification_queued(self):
        """Record notification queued due to rate limit"""
        notifications_queued_total.inc()

    def record_late_notification(self, delay_seconds: float):
        """Record late notification with delay"""
        late_notifications_total.inc()
        late_notification_delay_seconds.observe(delay_seconds)

    def update_consumer_lag(self, partition: int, lag: int):
        """Update consumer lag for partition"""
        consumer_lag.labels(partition=str(partition)).set(lag)

    def update_consumer_offset(self, partition: int, offset: int):
        """Update consumer offset for partition"""
        consumer_offset.labels(partition=str(partition)).set(offset)

    def set_kafka_connection_status(self, connected: bool):
        """Update Kafka connection status"""
        kafka_connection_status.set(1 if connected else 0)

    def set_web_push_api_status(self, available: bool):
        """Update Web Push API status"""
        web_push_api_status.set(1 if available else 0)

    def set_service_health(self, healthy: bool):
        """Update overall service health"""
        service_health.set(1 if healthy else 0)

    def update_active_subscriptions(self, count: int):
        """Update active subscriptions count"""
        active_subscriptions_total.set(count)

    def record_subscription_failure(self):
        """Record subscription lookup failure"""
        subscription_failures_total.inc()

    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format"""
        return generate_latest()

    def get_content_type(self) -> str:
        """Get Prometheus content type"""
        return CONTENT_TYPE_LATEST


# Global metrics collector instance
metrics_collector = MetricsCollector()
