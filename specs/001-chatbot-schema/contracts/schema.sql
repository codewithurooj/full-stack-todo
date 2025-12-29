-- =============================================================================
-- AI Chatbot Database Schema - Phase III
-- =============================================================================
-- Feature: 001-chatbot-schema
-- Date: 2025-12-27
-- Purpose: Add conversations and messages tables for AI chatbot functionality
--
-- This migration adds support for persistent conversation history to enable
-- stateless chat endpoints. Each conversation belongs to a user and contains
-- multiple messages exchanged between the user and the AI assistant.
--
-- Prerequisites:
--   - users table must exist (from Phase II)
--   - PostgreSQL 12+ (for proper CASCADE support)
--
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Table: conversations
-- -----------------------------------------------------------------------------
-- Purpose: Track chat sessions between users and the AI assistant
-- Lifecycle: Created on first message, updated on each new message, deleted
--            when user is deleted (CASCADE)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS conversations (
    -- Primary key: auto-incrementing conversation ID
    id SERIAL PRIMARY KEY,

    -- Foreign key: user who owns this conversation
    -- CASCADE DELETE: when user deleted, delete all their conversations
    user_id INTEGER NOT NULL,

    -- Timestamp: when this conversation was started
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Timestamp: when the last message was added to this conversation
    -- Updated every time a new message is created
    last_message_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key constraint
    CONSTRAINT fk_conversations_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    -- Business constraint: last message must be after or at conversation start
    CONSTRAINT check_last_message_after_start
        CHECK (last_message_at >= started_at)
);

-- Index for fast "get all conversations for user" queries
-- Supports: SELECT * FROM conversations WHERE user_id = ? ORDER BY last_message_at DESC
CREATE INDEX IF NOT EXISTS idx_conversations_user_id
    ON conversations(user_id);

-- Index for sorting by last activity
CREATE INDEX IF NOT EXISTS idx_conversations_last_message_at
    ON conversations(last_message_at DESC);

-- Comments for documentation
COMMENT ON TABLE conversations IS 'Chat sessions between users and AI assistant';
COMMENT ON COLUMN conversations.id IS 'Unique conversation identifier';
COMMENT ON COLUMN conversations.user_id IS 'User who owns this conversation (FK to users.id)';
COMMENT ON COLUMN conversations.started_at IS 'When conversation was created';
COMMENT ON COLUMN conversations.last_message_at IS 'When last message was added (updated on each message)';

-- -----------------------------------------------------------------------------
-- Table: messages
-- -----------------------------------------------------------------------------
-- Purpose: Store individual messages in conversations (user and assistant)
-- Lifecycle: Created when message sent, immutable after creation, deleted
--            when conversation is deleted (CASCADE)
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS messages (
    -- Primary key: auto-incrementing message ID
    id SERIAL PRIMARY KEY,

    -- Foreign key: conversation this message belongs to
    -- CASCADE DELETE: when conversation deleted, delete all messages
    conversation_id INTEGER NOT NULL,

    -- Role: who sent this message ('user' or 'assistant')
    -- CHECK constraint ensures only valid values
    role VARCHAR(20) NOT NULL,

    -- Content: the actual message text
    -- TEXT type supports messages up to 1GB (more than enough for 10k chars)
    content TEXT NOT NULL,

    -- Timestamp: when this message was created
    -- Immutable - never updated after creation
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Foreign key constraint
    CONSTRAINT fk_messages_conversation
        FOREIGN KEY (conversation_id)
        REFERENCES conversations(id)
        ON DELETE CASCADE,

    -- Business constraint: role must be 'user' or 'assistant'
    CONSTRAINT check_role_valid
        CHECK (role IN ('user', 'assistant')),

    -- Business constraint: content cannot be empty
    CONSTRAINT check_content_not_empty
        CHECK (LENGTH(TRIM(content)) > 0)
);

-- Index for fast "get all messages for conversation" queries
-- Supports: SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
    ON messages(conversation_id);

-- Composite index for efficient message retrieval with ordering
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created
    ON messages(conversation_id, created_at ASC);

-- Comments for documentation
COMMENT ON TABLE messages IS 'Individual messages in conversations (user and assistant messages)';
COMMENT ON COLUMN messages.id IS 'Unique message identifier';
COMMENT ON COLUMN messages.conversation_id IS 'Conversation this message belongs to (FK to conversations.id)';
COMMENT ON COLUMN messages.role IS 'Who sent this message: user or assistant';
COMMENT ON COLUMN messages.content IS 'Message text content (supports 10k+ characters)';
COMMENT ON COLUMN messages.created_at IS 'When message was created (immutable)';

-- =============================================================================
-- Verification Queries
-- =============================================================================
-- Run these after migration to verify schema was created correctly
-- =============================================================================

-- Verify conversations table structure
-- Expected: 4 columns (id, user_id, started_at, last_message_at)
-- \d conversations

-- Verify messages table structure
-- Expected: 5 columns (id, conversation_id, role, content, created_at)
-- \d messages

-- Verify foreign key constraints exist
-- Expected: 2 constraints (fk_conversations_user, fk_messages_conversation)
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
JOIN information_schema.referential_constraints AS rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_name IN ('conversations', 'messages');

-- Verify indexes exist
-- Expected: 4 indexes (2 on conversations, 2 on messages, plus PKs)
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('conversations', 'messages')
ORDER BY tablename, indexname;

-- Verify CHECK constraints exist
-- Expected: 3 constraints (check_last_message_after_start, check_role_valid, check_content_not_empty)
SELECT
    tc.constraint_name,
    tc.table_name,
    cc.check_clause
FROM information_schema.table_constraints AS tc
JOIN information_schema.check_constraints AS cc
    ON tc.constraint_name = cc.constraint_name
WHERE tc.constraint_type = 'CHECK'
    AND tc.table_name IN ('conversations', 'messages')
ORDER BY tc.table_name, tc.constraint_name;

-- =============================================================================
-- Rollback / Downgrade Script
-- =============================================================================
-- Use this to revert the migration if needed
-- WARNING: This will delete all conversation and message data!
-- =============================================================================

-- DROP TABLE IF EXISTS messages CASCADE;
-- DROP TABLE IF EXISTS conversations CASCADE;

-- =============================================================================
-- Sample Data for Testing
-- =============================================================================
-- Uncomment to insert test data (assumes user_id=1 exists)
-- =============================================================================

/*
-- Create a test conversation
INSERT INTO conversations (user_id, started_at, last_message_at)
VALUES (1, NOW(), NOW())
RETURNING id;

-- Insert test messages (replace 1 with actual conversation_id from above)
INSERT INTO messages (conversation_id, role, content, created_at)
VALUES
    (1, 'user', 'Hello, can you help me create a task?', NOW()),
    (1, 'assistant', 'Of course! I can help you create a task. What would you like to add?', NOW() + INTERVAL '1 second'),
    (1, 'user', 'Add a task to buy groceries', NOW() + INTERVAL '2 seconds'),
    (1, 'assistant', 'I''ve added "Buy groceries" to your task list.', NOW() + INTERVAL '3 seconds');

-- Update conversation's last_message_at
UPDATE conversations
SET last_message_at = NOW() + INTERVAL '3 seconds'
WHERE id = 1;

-- Verify the data
SELECT * FROM conversations WHERE id = 1;
SELECT * FROM messages WHERE conversation_id = 1 ORDER BY created_at;
*/

-- =============================================================================
-- Performance Testing Queries
-- =============================================================================
-- Use these to verify performance meets success criteria
-- =============================================================================

/*
-- Test: Get all conversations for user (should be < 100ms for 100 conversations)
EXPLAIN ANALYZE
SELECT * FROM conversations
WHERE user_id = 1
ORDER BY last_message_at DESC;

-- Test: Get all messages for conversation (should be < 50ms for 50 messages)
EXPLAIN ANALYZE
SELECT * FROM messages
WHERE conversation_id = 1
ORDER BY created_at ASC;

-- Test: Get latest 10 messages for conversation
EXPLAIN ANALYZE
SELECT * FROM messages
WHERE conversation_id = 1
ORDER BY created_at DESC
LIMIT 10;

-- Test: Count messages in conversation
EXPLAIN ANALYZE
SELECT COUNT(*) FROM messages
WHERE conversation_id = 1;
*/
