/**
 * Chat API Client
 * Handles chat endpoint requests with authentication
 */

import { ChatRequest, ChatResponse } from '@/types/chat'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Base fetch wrapper for chat API
 */
async function chatApiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
    credentials: 'include', // Send httpOnly cookies with JWT
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { message: 'An error occurred' },
    }))
    throw new Error(error.error?.message || error.detail || 'API request failed')
  }

  return response.json()
}

/**
 * Chat API Methods
 */
export const chatApi = {
  /**
   * Send a chat message and get AI response
   * POST /api/{user_id}/chat
   */
  async sendMessage(userId: string, data: ChatRequest): Promise<ChatResponse> {
    return chatApiFetch<ChatResponse>(`/api/${userId}/chat`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
}
