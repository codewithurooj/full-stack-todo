"""
Dapr State Store Operations
Feature: 012-dapr-integration
Purpose: Manage conversation state using Dapr state store (PostgreSQL backend)
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from app.config import settings
from app.services.dapr_client import get_dapr_client

logger = logging.getLogger(__name__)


class Message(BaseModel):
    """Chat message in a conversation"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ConversationContext(BaseModel):
    """Context for a conversation"""
    last_tool_call: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    active_task_id: Optional[int] = None


class ConversationState(BaseModel):
    """Full conversation state"""
    user_id: str
    messages: List[Message] = []
    context: ConversationContext = ConversationContext()
    created_at: str
    updated_at: str


class DaprStateService:
    """
    Service for managing conversation state via Dapr state store.
    Uses PostgreSQL as the backend through Dapr's state.postgresql component.
    """

    def __init__(self, store_name: str = None):
        self.store_name = store_name or settings.DAPR_STATESTORE_NAME

    def _get_key(self, conversation_id: str) -> str:
        """Generate state key for a conversation"""
        return f"conversation-{conversation_id}"

    async def get_conversation_state(
        self,
        conversation_id: str
    ) -> tuple[Optional[ConversationState], Optional[str]]:
        """
        Get conversation state from Dapr state store.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            Tuple of (ConversationState, etag) or (None, None) if not found
        """
        client = get_dapr_client()
        key = self._get_key(conversation_id)

        value, etag = await client.get_state(self.store_name, key)

        if value is None:
            logger.debug(f"Conversation state not found: {conversation_id}")
            return None, None

        try:
            state = ConversationState(**value)
            logger.debug(f"Retrieved conversation state: {conversation_id}, messages={len(state.messages)}")
            return state, etag
        except Exception as e:
            logger.error(f"Error parsing conversation state: {e}")
            return None, None

    async def save_conversation_state(
        self,
        conversation_id: str,
        state: ConversationState,
        etag: Optional[str] = None
    ) -> bool:
        """
        Save conversation state to Dapr state store.

        Args:
            conversation_id: Unique conversation identifier
            state: Conversation state to save
            etag: Optional etag for optimistic locking

        Returns:
            True if save succeeded, False otherwise
        """
        client = get_dapr_client()
        key = self._get_key(conversation_id)

        # Update timestamp
        state.updated_at = datetime.now(timezone.utc).isoformat()

        success = await client.save_state(
            self.store_name,
            key,
            state.model_dump(),
            etag=etag
        )

        if success:
            logger.debug(f"Saved conversation state: {conversation_id}")
        else:
            logger.error(f"Failed to save conversation state: {conversation_id}")

        return success

    async def create_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> ConversationState:
        """
        Create a new conversation state.

        Args:
            conversation_id: Unique conversation identifier
            user_id: User who owns the conversation

        Returns:
            New ConversationState
        """
        now = datetime.now(timezone.utc).isoformat()
        state = ConversationState(
            user_id=user_id,
            messages=[],
            context=ConversationContext(),
            created_at=now,
            updated_at=now
        )

        await self.save_conversation_state(conversation_id, state)
        logger.info(f"Created new conversation: {conversation_id} for user {user_id}")

        return state

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Add a message to an existing conversation.

        Args:
            conversation_id: Conversation to add message to
            role: Message role (user, assistant, system)
            content: Message content
            tool_calls: Optional tool calls for assistant messages

        Returns:
            True if message added successfully, False otherwise
        """
        state, etag = await self.get_conversation_state(conversation_id)

        if state is None:
            logger.warning(f"Cannot add message: conversation {conversation_id} not found")
            return False

        # Create new message
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
            tool_calls=tool_calls
        )

        # Append message
        state.messages.append(message)

        # Limit conversation history (keep last N messages)
        max_messages = settings.CHAT_HISTORY_LIMIT
        if len(state.messages) > max_messages:
            state.messages = state.messages[-max_messages:]

        return await self.save_conversation_state(conversation_id, state, etag)

    async def update_context(
        self,
        conversation_id: str,
        last_tool_call: Optional[str] = None,
        active_task_id: Optional[int] = None,
        preferences: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update conversation context.

        Args:
            conversation_id: Conversation to update
            last_tool_call: Last tool that was called
            active_task_id: Currently discussed task ID
            preferences: User preferences

        Returns:
            True if updated successfully, False otherwise
        """
        state, etag = await self.get_conversation_state(conversation_id)

        if state is None:
            logger.warning(f"Cannot update context: conversation {conversation_id} not found")
            return False

        if last_tool_call is not None:
            state.context.last_tool_call = last_tool_call
        if active_task_id is not None:
            state.context.active_task_id = active_task_id
        if preferences is not None:
            state.context.preferences = preferences

        return await self.save_conversation_state(conversation_id, state, etag)

    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation state.

        Args:
            conversation_id: Conversation to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        client = get_dapr_client()
        key = self._get_key(conversation_id)

        success = await client.delete_state(self.store_name, key)

        if success:
            logger.info(f"Deleted conversation: {conversation_id}")
        else:
            logger.warning(f"Failed to delete conversation: {conversation_id}")

        return success

    async def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get messages from a conversation.

        Args:
            conversation_id: Conversation to get messages from
            limit: Optional limit on number of messages

        Returns:
            List of messages (empty if conversation not found)
        """
        state, _ = await self.get_conversation_state(conversation_id)

        if state is None:
            return []

        messages = state.messages
        if limit:
            messages = messages[-limit:]

        return messages


# In-memory fallback for when Dapr is unavailable
_in_memory_state: Dict[str, ConversationState] = {}


class InMemoryStateService:
    """
    Fallback in-memory state service when Dapr is unavailable.
    Used for local development without Dapr.
    """

    async def get_conversation_state(
        self,
        conversation_id: str
    ) -> tuple[Optional[ConversationState], Optional[str]]:
        key = f"conversation-{conversation_id}"
        if key in _in_memory_state:
            return _in_memory_state[key], None
        return None, None

    async def save_conversation_state(
        self,
        conversation_id: str,
        state: ConversationState,
        etag: Optional[str] = None
    ) -> bool:
        key = f"conversation-{conversation_id}"
        state.updated_at = datetime.now(timezone.utc).isoformat()
        _in_memory_state[key] = state
        return True

    async def create_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> ConversationState:
        now = datetime.now(timezone.utc).isoformat()
        state = ConversationState(
            user_id=user_id,
            messages=[],
            context=ConversationContext(),
            created_at=now,
            updated_at=now
        )
        await self.save_conversation_state(conversation_id, state)
        return state

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        state, _ = await self.get_conversation_state(conversation_id)
        if state is None:
            return False

        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(timezone.utc).isoformat(),
            tool_calls=tool_calls
        )
        state.messages.append(message)

        max_messages = settings.CHAT_HISTORY_LIMIT
        if len(state.messages) > max_messages:
            state.messages = state.messages[-max_messages:]

        return await self.save_conversation_state(conversation_id, state)

    async def delete_conversation(self, conversation_id: str) -> bool:
        key = f"conversation-{conversation_id}"
        if key in _in_memory_state:
            del _in_memory_state[key]
        return True

    async def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Message]:
        state, _ = await self.get_conversation_state(conversation_id)
        if state is None:
            return []
        messages = state.messages
        if limit:
            messages = messages[-limit:]
        return messages


# Global state service instance
_state_service: Optional[DaprStateService] = None


def get_state_service():
    """Get the appropriate state service based on Dapr availability."""
    global _state_service

    if settings.DAPR_ENABLED:
        if _state_service is None:
            _state_service = DaprStateService()
        return _state_service
    else:
        # Use in-memory fallback
        return InMemoryStateService()
