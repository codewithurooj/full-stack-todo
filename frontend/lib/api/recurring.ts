/**
 * Recurring Tasks API
 * API methods for managing recurring task patterns
 */

import { Task } from '@/types/task'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * API Error class with detailed information
 */
export class ApiError extends Error {
  status: number
  code?: string
  details?: any

  constructor(message: string, status: number, code?: string, details?: any) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

/**
 * Base fetch wrapper with authentication via cookies
 */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include', // Automatically send httpOnly cookies
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'An error occurred' },
      }))

      const message =
        error.error?.message ||
        error.detail ||
        error.message ||
        `Request failed with status ${response.status}`

      throw new ApiError(
        message,
        response.status,
        error.error?.code,
        error.error?.details || error
      )
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return null as T
    }

    return response.json()
  } catch (err) {
    if (err instanceof ApiError) {
      throw err
    }

    if (err instanceof Error) {
      throw new ApiError(
        err.message || 'Network error occurred',
        0,
        'NETWORK_ERROR'
      )
    }

    throw new ApiError('An unknown error occurred', 0, 'UNKNOWN_ERROR')
  }
}

/**
 * Recurring Task API Methods
 */
export const recurringApi = {
  /**
   * Set recurring pattern on a task
   */
  async setRecurring(
    userId: string,
    taskId: number,
    pattern: 'daily' | 'weekly' | 'monthly' | 'custom',
    interval?: number,
    days?: string[],
    endDate?: string
  ): Promise<Task> {
    const body: any = {
      pattern,
      interval: interval || 1,
    }

    if (days && days.length > 0) {
      body.days = days
    }

    if (endDate) {
      body.end_date = endDate
    }

    return apiFetch<Task>(`/api/${userId}/tasks/${taskId}/recurring`, {
      method: 'PUT',
      body: JSON.stringify(body),
    })
  },

  /**
   * Remove recurring pattern from a task
   */
  async removeRecurring(
    userId: string,
    taskId: number,
    deleteType?: 'this_only' | 'this_and_future' | 'all'
  ): Promise<void> {
    const params = deleteType ? `?delete_type=${deleteType}` : ''
    return apiFetch<void>(`/api/${userId}/tasks/${taskId}/recurring${params}`, {
      method: 'DELETE',
    })
  },

  /**
   * Calculate next occurrence of a recurring task
   */
  async getNextOccurrence(
    userId: string,
    taskId: number
  ): Promise<{ next_occurrence: string }> {
    return apiFetch<{ next_occurrence: string }>(
      `/api/${userId}/tasks/${taskId}/recurring/next`
    )
  },
}
