/**
 * Due Dates API
 * API methods for managing task due dates
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
 * Due Date API Methods
 */
export const dueDateApi = {
  /**
   * Set due date for a task
   */
  async setDueDate(
    userId: string,
    taskId: number,
    dueDate: string,
    timezone?: string
  ): Promise<Task> {
    return apiFetch<Task>(`/api/${userId}/tasks/${taskId}/due-date`, {
      method: 'PUT',
      body: JSON.stringify({
        due_date: dueDate,
        timezone: timezone || Intl.DateTimeFormat().resolvedOptions().timeZone,
      }),
    })
  },

  /**
   * Clear due date for a task
   */
  async clearDueDate(userId: string, taskId: number): Promise<void> {
    return apiFetch<void>(`/api/${userId}/tasks/${taskId}/due-date`, {
      method: 'DELETE',
    })
  },

  /**
   * Filter tasks by due date range
   */
  async filterTasksByDueDate(
    userId: string,
    range: 'today' | 'this_week' | 'this_month' | 'overdue'
  ): Promise<Task[]> {
    return apiFetch<Task[]>(`/api/${userId}/tasks?relative_range=${range}`)
  },

  /**
   * Get tasks with due dates in a specific date range
   */
  async getTasksByDateRange(
    userId: string,
    dateFrom: string,
    dateTo: string
  ): Promise<Task[]> {
    return apiFetch<Task[]>(
      `/api/${userId}/tasks?date_from=${dateFrom}&date_to=${dateTo}`
    )
  },

  /**
   * Get overdue tasks
   */
  async getOverdueTasks(userId: string): Promise<Task[]> {
    return apiFetch<Task[]>(`/api/${userId}/tasks?relative_range=overdue`)
  },

  /**
   * Get tasks due today
   */
  async getTodayTasks(userId: string): Promise<Task[]> {
    return apiFetch<Task[]>(`/api/${userId}/tasks?relative_range=today`)
  },

  /**
   * Get tasks due this week
   */
  async getThisWeekTasks(userId: string): Promise<Task[]> {
    return apiFetch<Task[]>(`/api/${userId}/tasks?relative_range=this_week`)
  },

  /**
   * Get tasks due this month
   */
  async getThisMonthTasks(userId: string): Promise<Task[]> {
    return apiFetch<Task[]>(`/api/${userId}/tasks?relative_range=this_month`)
  },
}
