-- Migration 001: Create notification service tables
-- Description: Create tables for notification logs, push subscriptions, and user stats

-- Notification logs table
CREATE TABLE IF NOT EXISTS notification_logs (
    id SERIAL PRIMARY KEY,
    reminder_id VARCHAR(255) NOT NULL,
    task_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    sent_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) NOT NULL,
    error_message TEXT,

    -- Indexes for common queries
    INDEX idx_notification_logs_reminder_id (reminder_id),
    INDEX idx_notification_logs_task_id (task_id),
    INDEX idx_notification_logs_user_id (user_id),
    INDEX idx_notification_logs_sent_at (sent_at),
    INDEX idx_notification_logs_status (status)
);

-- Push subscriptions table
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    endpoint VARCHAR(500) UNIQUE NOT NULL,
    p256dh VARCHAR(255) NOT NULL,
    auth VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    active BOOLEAN DEFAULT TRUE,

    -- Indexes
    INDEX idx_push_subscriptions_user_id (user_id),
    INDEX idx_push_subscriptions_endpoint (endpoint),
    INDEX idx_push_subscriptions_active (active)
);

-- User notification stats table (for rate limiting)
CREATE TABLE IF NOT EXISTS user_notification_stats (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,
    notification_count INTEGER DEFAULT 0,
    window_start TIMESTAMP DEFAULT NOW(),

    -- Index
    INDEX idx_user_notification_stats_user_id (user_id)
);

-- Add reminded column to tasks table if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tasks' AND column_name = 'reminded'
    ) THEN
        ALTER TABLE tasks ADD COLUMN reminded BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Comments
COMMENT ON TABLE notification_logs IS 'Logs all notification attempts';
COMMENT ON TABLE push_subscriptions IS 'Web Push subscription endpoints for users';
COMMENT ON TABLE user_notification_stats IS 'Rate limiting statistics per user';
COMMENT ON COLUMN tasks.reminded IS 'Whether user has been reminded about this task';
