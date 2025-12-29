'use client'

import { useState, useCallback, useEffect } from 'react'
import { ChatState, Message } from '@/types/chat'
import { chatApi } from '@/lib/api/chat'

const CONVERSATION_KEY_PREFIX = 'chat_conversation_'
const MESSAGES_LIMIT = 50 // T026: 50-message display limit

/**
 * useChatState Hook
 * T017: Manages chat state (messages, loading, error, conversation ID)
 * T018: Handles API integration for sending messages
 * T020-T022: Conversation ID state management and persistence
 * T024: Handle page reload with conversation persistence
 */
export function useChatState(userId: string) {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
    conversationId: null,
  })

  // T021: Load conversation history on mount (from localStorage)
  // T024: Page reload with conversation persistence
  useEffect(() => {
    const storageKey = `${CONVERSATION_KEY_PREFIX}${userId}`
    const stored = localStorage.getItem(storageKey)

    if (stored) {
      try {
        const data = JSON.parse(stored)
        setState((prev) => ({
          ...prev,
          conversationId: data.conversationId,
          messages: data.messages.slice(-MESSAGES_LIMIT), // T026: Limit to 50 messages
        }))
      } catch (e) {
        // Invalid data, clear it
        localStorage.removeItem(storageKey)
      }
    }
  }, [userId])

  // Save conversation to localStorage whenever it changes
  useEffect(() => {
    if (state.conversationId && state.messages.length > 0) {
      const storageKey = `${CONVERSATION_KEY_PREFIX}${userId}`
      const data = {
        conversationId: state.conversationId,
        messages: state.messages.slice(-MESSAGES_LIMIT), // T026: Limit stored messages
      }
      localStorage.setItem(storageKey, JSON.stringify(data))
    }
  }, [state.conversationId, state.messages, userId])

  /**
   * Send a message to the AI assistant
   * T018: API integration to send messages
   * T022: Include conversation_id in API requests
   */
  const sendMessage = useCallback(
    async (content: string) => {
      try {
        // Clear any previous errors
        setState((prev) => ({
          ...prev,
          isLoading: true,
          error: null,
        }))

        // Add user message to UI immediately
        const userMessage: Message = {
          role: 'user',
          content,
          created_at: new Date().toISOString(),
        }

        setState((prev) => ({
          ...prev,
          messages: [...prev.messages, userMessage],
        }))

        // T022: Call API with conversation_id if available
        const response = await chatApi.sendMessage(userId, {
          message: content,
          conversation_id: state.conversationId || undefined,
        })

        // Add assistant message to UI
        const assistantMessage: Message = {
          role: 'assistant',
          content: response.assistant_message,
          created_at: response.created_at,
          tool_calls: response.tool_calls,
        }

        setState((prev) => ({
          ...prev,
          messages: [...prev.messages, assistantMessage],
          isLoading: false,
          conversationId: response.conversation_id,
        }))
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to send message'

        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: errorMessage,
        }))
      }
    },
    [userId, state.conversationId]
  )

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setState((prev) => ({
      ...prev,
      error: null,
    }))
  }, [])

  /**
   * T027: Start a new conversation
   */
  const startNewConversation = useCallback(() => {
    const storageKey = `${CONVERSATION_KEY_PREFIX}${userId}`
    localStorage.removeItem(storageKey)

    setState({
      messages: [],
      isLoading: false,
      error: null,
      conversationId: null,
    })
  }, [userId])

  /**
   * Reset chat state (alias for startNewConversation)
   */
  const resetChat = useCallback(() => {
    startNewConversation()
  }, [startNewConversation])

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    error: state.error,
    conversationId: state.conversationId,
    sendMessage,
    clearError,
    resetChat,
    startNewConversation,
  }
}
