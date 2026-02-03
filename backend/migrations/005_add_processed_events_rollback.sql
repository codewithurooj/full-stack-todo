-- Rollback Migration 005: Remove processed_events table
-- Feature: 012-dapr-integration

-- Drop cleanup function
DROP FUNCTION IF EXISTS cleanup_old_processed_events();

-- Drop indexes
DROP INDEX IF EXISTS idx_processed_events_service;
DROP INDEX IF EXISTS idx_processed_events_date;
DROP INDEX IF EXISTS idx_processed_events_topic;

-- Drop table
DROP TABLE IF EXISTS processed_events;
