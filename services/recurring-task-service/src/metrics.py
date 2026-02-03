"""
Prometheus Metrics for Recurring Task Service
Exports metrics for monitoring consumer health and performance
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging

logger = logging.getLogger(__name__)

# Consumer metrics
events_consumed_total = Counter(
    'recurring_task_events_consumed_total',
    'Total number of task.completed events consumed',
    ['event_type']
)

instances_created_total = Counter(
    'recurring_task_instances_created_total',
    'Total number of recurring task instances created'
)

instances_creation_failures_total = Counter(
    'recurring_task_instances_creation_failures_total',
    'Total number of failed instance creations',
    ['error_type']
)

# Idempotency metrics
duplicate_events_skipped_total = Counter(
    'recurring_task_duplicate_events_skipped_total',
    'Total number of duplicate events skipped (idempotency working)'
)

# Performance metrics
event_processing_duration_seconds = Histogram(
    'recurring_task_event_processing_duration_seconds',
    'Time spent processing each event',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

instance_creation_duration_seconds = Histogram(
    'recurring_task_instance_creation_duration_seconds',
    'Time spent creating task instance (DB insert)',
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# Consumer lag metrics
consumer_lag = Gauge(
    'recurring_task_consumer_lag',
    'Consumer lag (events behind)',
    ['partition']
)

consumer_offset = Gauge(
    'recurring_task_consumer_offset',
    'Current consumer offset',
    ['partition']
)

# Health metrics
service_health = Gauge(
    'recurring_task_service_health',
    'Service health status (1=healthy, 0=unhealthy)'
)

kafka_connection_status = Gauge(
    'recurring_task_kafka_connection_status',
    'Kafka connection status (1=connected, 0=disconnected)'
)

database_connection_status = Gauge(
    'recurring_task_database_connection_status',
    'Database connection status (1=connected, 0=disconnected)'
)

# Business metrics
active_recurring_patterns_total = Gauge(
    'recurring_task_active_patterns_total',
    'Total number of active recurring patterns',
    ['pattern_type']  # daily, weekly, monthly
)

end_date_reached_total = Counter(
    'recurring_task_end_date_reached_total',
    'Total number of recurring patterns that reached end_date'
)


class MetricsCollector:
    """Collects and manages metrics for Recurring Task Service"""

    def __init__(self):
        # Initialize health to healthy
        service_health.set(1)

    def record_event_consumed(self, event_type: str):
        """Record event consumption"""
        events_consumed_total.labels(event_type=event_type).inc()

    def record_instance_created(self):
        """Record successful instance creation"""
        instances_created_total.inc()

    def record_instance_creation_failure(self, error_type: str):
        """Record instance creation failure"""
        instances_creation_failures_total.labels(error_type=error_type).inc()

    def record_duplicate_event(self):
        """Record duplicate event skipped"""
        duplicate_events_skipped_total.inc()

    def record_event_processing_time(self, duration_seconds: float):
        """Record event processing duration"""
        event_processing_duration_seconds.observe(duration_seconds)

    def record_instance_creation_time(self, duration_seconds: float):
        """Record instance creation duration"""
        instance_creation_duration_seconds.observe(duration_seconds)

    def update_consumer_lag(self, partition: int, lag: int):
        """Update consumer lag for partition"""
        consumer_lag.labels(partition=str(partition)).set(lag)

    def update_consumer_offset(self, partition: int, offset: int):
        """Update consumer offset for partition"""
        consumer_offset.labels(partition=str(partition)).set(offset)

    def set_kafka_connection_status(self, connected: bool):
        """Update Kafka connection status"""
        kafka_connection_status.set(1 if connected else 0)

    def set_database_connection_status(self, connected: bool):
        """Update database connection status"""
        database_connection_status.set(1 if connected else 0)

    def set_service_health(self, healthy: bool):
        """Update overall service health"""
        service_health.set(1 if healthy else 0)

    def record_end_date_reached(self):
        """Record recurring pattern reaching end_date"""
        end_date_reached_total.inc()

    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format"""
        return generate_latest()

    def get_content_type(self) -> str:
        """Get Prometheus content type"""
        return CONTENT_TYPE_LATEST


# Global metrics collector instance
metrics_collector = MetricsCollector()
