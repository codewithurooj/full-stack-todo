/**
 * API Client with Authentication
 * Handles all backend API requests with JWT tokens from Better Auth cookies
 */

import { Task, TaskCreate, TaskUpdate } from '@/types/task'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Base fetch wrapper with authentication via cookies
 *
 * Better Auth stores the JWT token in an httpOnly cookie (better-auth.session_token)
 * which is automatically sent with every request when credentials: 'include' is set.
 * The backend reads this cookie to authenticate requests.
 */
async function apiFetch<T>(
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
    credentials: 'include', // Automatically send httpOnly cookies (including better-auth.session_token)
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: { message: 'An error occurred' },
    }))
    throw new Error(error.error?.message || error.detail || 'API request failed')
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as T
  }

  return response.json()
}

/**
 * Task API Methods
 */
export const taskApi = {
  /**
   * List all tasks for user
   */
  async list(userId: string): Promise<Task[]> {
    return apiFetch<Task[]>(`/api/${userId}/tasks`)
  },

  /**
   * Get a single task
   */
  async get(userId: string, taskId: number): Promise<Task> {
    return apiFetch<Task>(`/api/${userId}/tasks/${taskId}`)
  },

  /**
   * Create a new task
   */
  async create(userId: string, data: TaskCreate): Promise<Task> {
    return apiFetch<Task>(`/api/${userId}/tasks`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * Update a task
   */
  async update(userId: string, taskId: number, data: TaskUpdate): Promise<Task> {
    return apiFetch<Task>(`/api/${userId}/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  /**
   * Delete a task
   */
  async delete(userId: string, taskId: number): Promise<void> {
    return apiFetch<void>(`/api/${userId}/tasks/${taskId}`, {
      method: 'DELETE',
    })
  },

  /**
   * Toggle task completion
   */
  async toggleComplete(userId: string, taskId: number): Promise<Task> {
    return apiFetch<Task>(`/api/${userId}/tasks/${taskId}/complete`, {
      method: 'PATCH',
    })
  },
}

/**
 * Health Check
 */
export async function checkHealth(): Promise<{ status: string }> {
  return apiFetch<{ status: string }>('/health')
}
