-- Migration 005: Add processed_events table for Dapr event idempotency
-- Feature: 012-dapr-integration
-- Purpose: Track processed event IDs to ensure at-least-once delivery becomes exactly-once

-- Create processed_events table for idempotency tracking
-- This table is used by event subscription handlers to prevent duplicate processing
CREATE TABLE IF NOT EXISTS processed_events (
    event_id VARCHAR(36) PRIMARY KEY,
    topic VARCHAR(100) NOT NULL,
    service_name VARCHAR(100) NOT NULL DEFAULT 'backend-service',
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT check_event_id CHECK (event_id ~ '^[0-9a-f-]{36}$')
);

-- Index for efficient lookups by topic
CREATE INDEX IF NOT EXISTS idx_processed_events_topic ON processed_events(topic);

-- Index for cleanup queries (events older than retention period)
CREATE INDEX IF NOT EXISTS idx_processed_events_date ON processed_events(processed_at);

-- Index for service-specific queries
CREATE INDEX IF NOT EXISTS idx_processed_events_service ON processed_events(service_name);

-- Comment explaining the table
COMMENT ON TABLE processed_events IS 'Tracks processed event IDs for Dapr pub/sub idempotency. Events are retained for 7 days.';
COMMENT ON COLUMN processed_events.event_id IS 'UUID v4 event identifier from CloudEvent';
COMMENT ON COLUMN processed_events.topic IS 'Kafka/Dapr topic the event came from';
COMMENT ON COLUMN processed_events.service_name IS 'Service that processed this event';
COMMENT ON COLUMN processed_events.processed_at IS 'Timestamp when event was processed';
COMMENT ON COLUMN processed_events.metadata IS 'Optional metadata about the event processing';

-- Create a function to clean up old processed events (run daily via scheduler)
-- Retains events for 7 days to handle delayed retries
CREATE OR REPLACE FUNCTION cleanup_old_processed_events()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM processed_events
    WHERE processed_at < NOW() - INTERVAL '7 days';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_processed_events() IS 'Removes processed events older than 7 days';
