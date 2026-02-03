/**
 * Reminders API
 * API methods for managing task reminders
 */

import { Reminder, ReminderCreate } from '@/types/task'

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
 * Reminder API Methods
 */
export const reminderApi = {
  /**
   * Create reminder with offset in minutes
   */
  async createReminder(
    userId: string,
    taskId: number,
    offsetMinutes: number
  ): Promise<Reminder> {
    return apiFetch<Reminder>(
      `/api/${userId}/tasks/${taskId}/reminders`,
      {
        method: 'POST',
        body: JSON.stringify({ offset_minutes: offsetMinutes }),
      }
    )
  },

  /**
   * List reminders for a task
   */
  async listReminders(userId: string, taskId: number): Promise<Reminder[]> {
    return apiFetch<Reminder[]>(`/api/${userId}/tasks/${taskId}/reminders`)
  },

  /**
   * Delete reminder
   */
  async deleteReminder(
    userId: string,
    taskId: number,
    reminderId: number
  ): Promise<void> {
    return apiFetch<void>(
      `/api/${userId}/tasks/${taskId}/reminders/${reminderId}`,
      {
        method: 'DELETE',
      }
    )
  },

  /**
   * Snooze reminder for N minutes (default 10 minutes)
   */
  async snoozeReminder(
    userId: string,
    taskId: number,
    reminderId: number,
    snoozeMinutes: number = 10
  ): Promise<Reminder> {
    return apiFetch<Reminder>(
      `/api/${userId}/tasks/${taskId}/reminders/${reminderId}/snooze`,
      {
        method: 'POST',
        body: JSON.stringify({ snooze_minutes: snoozeMinutes }),
      }
    )
  },
}
