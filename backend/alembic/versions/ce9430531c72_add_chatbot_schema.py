"""add_chatbot_schema

Revision ID: ce9430531c72
Revises: 
Create Date: 2025-12-27 13:55:39.716269

Add conversations and messages tables for AI chatbot functionality.
Enables stateless chat endpoints with persistent conversation history.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce9430531c72'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create conversations and messages tables"""
    
    # =========================================================================
    # USER STORY 1: Conversations Table
    # =========================================================================
    
    # T009: Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('last_message_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        
        # T010: Foreign key constraint conversations.user_id → users.id with CASCADE
        sa.ForeignKeyConstraint(
            ['user_id'], ['users.id'],
            name='fk_conversations_user',
            ondelete='CASCADE'
        ),
        
        # T011: CHECK constraint (last_message_at >= started_at)
        sa.CheckConstraint(
            'last_message_at >= started_at',
            name='check_last_message_after_start'
        ),
    )
    
    # T012: Create index idx_conversations_user_id
    op.create_index('idx_conversations_user_id', 'conversations', ['user_id'])
    
    # T013: Create index idx_conversations_last_message_at (DESC)
    op.create_index(
        'idx_conversations_last_message_at',
        'conversations',
        [sa.text('last_message_at DESC')]
    )
    
    # =========================================================================
    # USER STORY 2: Messages Table
    # =========================================================================
    
    # T018: Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        
        # T019: Foreign key constraint messages.conversation_id → conversations.id with CASCADE
        sa.ForeignKeyConstraint(
            ['conversation_id'], ['conversations.id'],
            name='fk_messages_conversation',
            ondelete='CASCADE'
        ),
        
        # T020: CHECK constraint role IN ('user', 'assistant')
        sa.CheckConstraint(
            "role IN ('user', 'assistant')",
            name='check_role_valid'
        ),
    )
    
    # T021: Create index idx_messages_conversation_id
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    
    # T022: Create composite index idx_messages_conversation_created
    op.create_index(
        'idx_messages_conversation_created',
        'messages',
        ['conversation_id', sa.text('created_at ASC')]
    )


def downgrade() -> None:
    """Drop conversations and messages tables"""
    
    # T023: Drop messages table BEFORE conversations
    op.drop_index('idx_messages_conversation_created', 'messages')
    op.drop_index('idx_messages_conversation_id', 'messages')
    op.drop_table('messages')
    
    # T014: Drop conversations table
    op.drop_index('idx_conversations_last_message_at', 'conversations')
    op.drop_index('idx_conversations_user_id', 'conversations')
    op.drop_table('conversations')
