/**
 * Chat types for ChatKit UI
 * Aligned with backend API from Feature 003
 */

/**
 * Message interface
 * Represents a single message in the chat conversation
 */
export interface Message {
  id?: number
  conversation_id?: number
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at?: string
  tool_calls?: string[]
}

/**
 * Chat state interface
 * Manages the state of the chat UI
 */
export interface ChatState {
  messages: Message[]
  isLoading: boolean
  error: string | null
  conversationId: number | null
  isStreaming?: boolean
}

/**
 * Chat request interface
 * Payload sent to POST /api/{user_id}/chat
 */
export interface ChatRequest {
  message: string
  conversation_id?: number
}

/**
 * Chat response interface
 * Response from POST /api/{user_id}/chat
 */
export interface ChatResponse {
  conversation_id: number
  assistant_message: string
  tool_calls: string[]
  created_at: string
}

/**
 * Streaming chat event interface
 * For Server-Sent Events (SSE) streaming
 */
export interface StreamEvent {
  type: 'start' | 'token' | 'end' | 'error'
  content?: string
  error?: string
}
