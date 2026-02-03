/**
 * API Client with Authentication
 * Handles all backend API requests with JWT tokens from Better Auth cookies
 */

import { Task, TaskCreate, TaskUpdate, TaskFilters } from '@/types/task'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Build query string from filters object
 */
function buildQueryString(filters?: TaskFilters): string {
  if (!filters) return ''

  const params = new URLSearchParams()

  if (filters.priority) params.append('priority', filters.priority)
  if (filters.status && filters.status !== 'all') params.append('status', filters.status)
  if (filters.search) params.append('search', filters.search)
  if (filters.sort) params.append('sort_by', filters.sort)
  if (filters.order) params.append('sort_order', filters.order)
  if (filters.date_from) params.append('date_from', filters.date_from)
  if (filters.date_to) params.append('date_to', filters.date_to)

  // Handle tags array
  if (filters.tags && filters.tags.length > 0) {
    filters.tags.forEach(tag => params.append('tags', tag))
  }

  const queryString = params.toString()
  return queryString ? `?${queryString}` : ''
}

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

  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include', // Automatically send httpOnly cookies (including better-auth.session_token)
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        error: { message: 'An error occurred' },
      }))

      // Extract error message from various formats
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
    // Re-throw ApiError as-is
    if (err instanceof ApiError) {
      throw err
    }

    // Network errors or other exceptions
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
 * Task API Methods
 */
export const taskApi = {
  /**
   * List all tasks for user with optional filters
   */
  async list(userId: string, filters?: TaskFilters): Promise<Task[]> {
    const queryString = buildQueryString(filters)
    return apiFetch<Task[]>(`/api/${userId}/tasks${queryString}`)
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

  /**
   * Get unique tags for user
   */
  async getTags(userId: string): Promise<{ tags: string[], usage_count: Record<string, number> }> {
    return apiFetch<{ tags: string[], usage_count: Record<string, number> }>(`/api/${userId}/tasks/tags`)
  },
}

/**
 * Health Check
 */
export async function checkHealth(): Promise<{ status: string }> {
  return apiFetch<{ status: string }>('/health')
}
