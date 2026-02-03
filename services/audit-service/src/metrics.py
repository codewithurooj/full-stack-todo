"""
Prometheus Metrics for Audit Service
Exports metrics for monitoring audit log collection and performance
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import logging

logger = logging.getLogger(__name__)

# Consumer metrics
events_consumed_total = Counter(
    'audit_events_consumed_total',
    'Total number of events consumed',
    ['event_type']  # task.created, task.updated, etc.
)

audit_logs_inserted_total = Counter(
    'audit_audit_logs_inserted_total',
    'Total number of audit logs successfully inserted'
)

audit_log_insertion_failures_total = Counter(
    'audit_audit_log_insertion_failures_total',
    'Total number of failed audit log insertions',
    ['error_type']
)

# Idempotency metrics
duplicate_events_skipped_total = Counter(
    'audit_duplicate_events_skipped_total',
    'Total number of duplicate event_id events skipped'
)

# Batch processing metrics
batch_commits_total = Counter(
    'audit_batch_commits_total',
    'Total number of batch commits'
)

batch_size_histogram = Histogram(
    'audit_batch_size',
    'Number of audit logs per batch',
    buckets=[1, 10, 25, 50, 75, 100, 150, 200]
)

batch_commit_duration_seconds = Histogram(
    'audit_batch_commit_duration_seconds',
    'Time spent committing batch (DB insert + Kafka offset)',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

batch_timeout_commits_total = Counter(
    'audit_batch_timeout_commits_total',
    'Total number of batch commits triggered by timeout (vs size)'
)

# Performance metrics
event_processing_duration_seconds = Histogram(
    'audit_event_processing_duration_seconds',
    'Time spent processing each event',
    buckets=[0.0001, 0.0005, 0.001, 0.005, 0.01, 0.025, 0.05, 0.1]
)

pending_batch_size = Gauge(
    'audit_pending_batch_size',
    'Current size of pending batch (not yet committed)'
)

time_since_last_commit_seconds = Gauge(
    'audit_time_since_last_commit_seconds',
    'Time since last batch commit'
)

# Consumer lag metrics
consumer_lag = Gauge(
    'audit_consumer_lag',
    'Consumer lag (events behind)',
    ['partition']
)

consumer_offset = Gauge(
    'audit_consumer_offset',
    'Current consumer offset',
    ['partition']
)

# Health metrics
service_health = Gauge(
    'audit_service_health',
    'Service health status (1=healthy, 0=unhealthy)'
)

kafka_connection_status = Gauge(
    'audit_kafka_connection_status',
    'Kafka connection status (1=connected, 0=disconnected)'
)

database_connection_status = Gauge(
    'audit_database_connection_status',
    'Database connection status (1=connected, 0=disconnected)'
)

# Business metrics
system_generated_operations_total = Counter(
    'audit_system_generated_operations_total',
    'Total number of system-generated operations logged',
    ['operation_type']
)

user_generated_operations_total = Counter(
    'audit_user_generated_operations_total',
    'Total number of user-generated operations logged',
    ['operation_type']
)

total_audit_logs_count = Gauge(
    'audit_total_audit_logs_count',
    'Total number of audit logs in database (updated periodically)'
)


class MetricsCollector:
    """Collects and manages metrics for Audit Service"""

    def __init__(self):
        # Initialize health to healthy
        service_health.set(1)

    def record_event_consumed(self, event_type: str):
        """Record event consumption"""
        events_consumed_total.labels(event_type=event_type).inc()

    def record_audit_log_inserted(self):
        """Record successful audit log insertion"""
        audit_logs_inserted_total.inc()

    def record_audit_log_insertion_failure(self, error_type: str):
        """Record audit log insertion failure"""
        audit_log_insertion_failures_total.labels(error_type=error_type).inc()

    def record_duplicate_event(self):
        """Record duplicate event skipped"""
        duplicate_events_skipped_total.inc()

    def record_batch_commit(self, batch_size: int, duration_seconds: float, timeout_triggered: bool):
        """Record batch commit with size and duration"""
        batch_commits_total.inc()
        batch_size_histogram.observe(batch_size)
        batch_commit_duration_seconds.observe(duration_seconds)

        if timeout_triggered:
            batch_timeout_commits_total.inc()

    def record_event_processing_time(self, duration_seconds: float):
        """Record event processing duration"""
        event_processing_duration_seconds.observe(duration_seconds)

    def update_pending_batch_size(self, size: int):
        """Update current pending batch size"""
        pending_batch_size.set(size)

    def update_time_since_last_commit(self, seconds: float):
        """Update time since last commit"""
        time_since_last_commit_seconds.set(seconds)

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

    def record_operation(self, operation_type: str, system_generated: bool):
        """Record operation by type and source"""
        if system_generated:
            system_generated_operations_total.labels(operation_type=operation_type).inc()
        else:
            user_generated_operations_total.labels(operation_type=operation_type).inc()

    def update_total_audit_logs_count(self, count: int):
        """Update total audit logs count"""
        total_audit_logs_count.set(count)

    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format"""
        return generate_latest()

    def get_content_type(self) -> str:
        """Get Prometheus content type"""
        return CONTENT_TYPE_LATEST


# Global metrics collector instance
metrics_collector = MetricsCollector()
