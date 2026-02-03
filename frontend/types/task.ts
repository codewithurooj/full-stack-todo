/**
 * Task TypeScript Interfaces
 * Matches backend SQLModel schemas
 */

export interface Task {
  id: number
  user_id: string
  title: string
  description: string | null
  completed: boolean
  priority: 'high' | 'medium' | 'low'
  tags: string[]
  created_at: string
  updated_at: string
  due_date?: string | null  // ISO 8601 timestamp
  recurring_pattern?: string | null
  recurring_interval?: number | null
  recurring_days?: string[] | null
  recurring_end_date?: string | null
  parent_task_id?: number | null
  next_occurrence?: string | null
}

export interface TaskCreate {
  title: string
  description?: string
  priority?: 'high' | 'medium' | 'low'
  tags?: string[]
  due_date?: string
  timezone?: string
}

export interface TaskUpdate {
  title?: string
  description?: string
  completed?: boolean
  priority?: 'high' | 'medium' | 'low'
  tags?: string[]
  due_date?: string
  timezone?: string
}

export interface TaskFilters {
  status?: 'all' | 'pending' | 'completed'
  priority?: 'high' | 'medium' | 'low'
  tags?: string[]
  search?: string
  sort?: 'created_at' | 'updated_at' | 'title' | 'priority' | 'due_date'
  order?: 'asc' | 'desc'
  date_from?: string
  date_to?: string
  relative_range?: 'today' | 'this_week' | 'this_month' | 'overdue'
}

export interface Reminder {
  id: number
  task_id: number
  user_id: string
  remind_at: string  // ISO 8601
  offset_minutes: number
  delivered: boolean
  delivery_status: 'pending' | 'sent' | 'failed' | 'dismissed' | 'snoozed'
  created_at: string
  updated_at: string
}

export interface ReminderCreate {
  offset_minutes: number
}

export interface QueuedNotification {
  id: string
  title: string
  body: string
  timestamp: string
  taskId?: number
}
