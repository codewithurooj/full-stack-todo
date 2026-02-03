"""
Conversation State Service
Feature: 012-dapr-integration
Purpose: High-level service for managing chat conversation state using Dapr state store
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.config import settings
from app.services.dapr_state import (
    get_state_service,
    ConversationState,
    Message,
    ConversationContext
)

logger = logging.getLogger(__name__)


class ConversationStateService:
    """
    High-level service for managing conversation state.
    Wraps DaprStateService with additional business logic.
    """

    def __init__(self):
        self._state_service = None

    @property
    def state_service(self):
        """Lazy load state service"""
        if self._state_service is None:
            self._state_service = get_state_service()
        return self._state_service

    async def get_or_create_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> ConversationState:
        """
        Get existing conversation or create a new one.

        Args:
            conversation_id: Conversation identifier
            user_id: User who owns the conversation

        Returns:
            ConversationState (existing or newly created)
        """
        state, _ = await self.state_service.get_conversation_state(conversation_id)

        if state is not None:
            # Verify user owns this conversation
            if state.user_id != user_id:
                logger.warning(
                    f"User {user_id} attempted to access conversation "
                    f"{conversation_id} owned by {state.user_id}"
                )
                # Create new conversation for this user instead
                return await self.state_service.create_conversation(conversation_id, user_id)
            return state

        # Create new conversation
        return await self.state_service.create_conversation(conversation_id, user_id)

    async def add_user_message(
        self,
        conversation_id: str,
        content: str
    ) -> bool:
        """
        Add a user message to the conversation.

        Args:
            conversation_id: Conversation to add message to
            content: User message content

        Returns:
            True if added successfully
        """
        return await self.state_service.add_message(
            conversation_id=conversation_id,
            role="user",
            content=content
        )

    async def add_assistant_message(
        self,
        conversation_id: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Add an assistant message to the conversation.

        Args:
            conversation_id: Conversation to add message to
            content: Assistant message content
            tool_calls: Optional tool calls made by the assistant

        Returns:
            True if added successfully
        """
        return await self.state_service.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            tool_calls=tool_calls
        )

    async def add_system_message(
        self,
        conversation_id: str,
        content: str
    ) -> bool:
        """
        Add a system message to the conversation.

        Args:
            conversation_id: Conversation to add message to
            content: System message content

        Returns:
            True if added successfully
        """
        return await self.state_service.add_message(
            conversation_id=conversation_id,
            role="system",
            content=content
        )

    async def get_conversation_history(
        self,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history formatted for OpenAI API.

        Args:
            conversation_id: Conversation to get history for
            limit: Optional limit on number of messages

        Returns:
            List of message dicts in OpenAI format
        """
        messages = await self.state_service.get_messages(conversation_id, limit)

        # Convert to OpenAI message format
        openai_messages = []
        for msg in messages:
            message_dict = {
                "role": msg.role,
                "content": msg.content
            }
            if msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls
            openai_messages.append(message_dict)

        return openai_messages

    async def get_conversation_context(
        self,
        conversation_id: str
    ) -> Optional[ConversationContext]:
        """
        Get conversation context.

        Args:
            conversation_id: Conversation to get context for

        Returns:
            ConversationContext or None if not found
        """
        state, _ = await self.state_service.get_conversation_state(conversation_id)
        if state:
            return state.context
        return None

    async def update_conversation_context(
        self,
        conversation_id: str,
        last_tool_call: Optional[str] = None,
        active_task_id: Optional[int] = None
    ) -> bool:
        """
        Update conversation context after tool calls.

        Args:
            conversation_id: Conversation to update
            last_tool_call: Name of last tool called
            active_task_id: ID of task being discussed

        Returns:
            True if updated successfully
        """
        state, etag = await self.state_service.get_conversation_state(conversation_id)

        if state is None:
            return False

        if last_tool_call is not None:
            state.context.last_tool_call = last_tool_call
        if active_task_id is not None:
            state.context.active_task_id = active_task_id

        return await self.state_service.save_conversation_state(
            conversation_id, state, etag
        )

    async def clear_conversation(
        self,
        conversation_id: str
    ) -> bool:
        """
        Clear all messages from a conversation while keeping the conversation.

        Args:
            conversation_id: Conversation to clear

        Returns:
            True if cleared successfully
        """
        state, etag = await self.state_service.get_conversation_state(conversation_id)

        if state is None:
            return False

        state.messages = []
        state.context = ConversationContext()

        return await self.state_service.save_conversation_state(
            conversation_id, state, etag
        )

    async def delete_conversation(
        self,
        conversation_id: str
    ) -> bool:
        """
        Delete a conversation entirely.

        Args:
            conversation_id: Conversation to delete

        Returns:
            True if deleted successfully
        """
        return await self.state_service.delete_conversation(conversation_id)

    def generate_conversation_id(self, user_id: str) -> str:
        """
        Generate a unique conversation ID for a user.

        Args:
            user_id: User ID

        Returns:
            Unique conversation ID
        """
        return f"{user_id}-{uuid4().hex[:8]}"


# Global conversation state service instance
_conversation_service: Optional[ConversationStateService] = None


def get_conversation_state_service() -> ConversationStateService:
    """Get the global conversation state service instance."""
    global _conversation_service
    if _conversation_service is None:
        _conversation_service = ConversationStateService()
    return _conversation_service
