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
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  title: string
  description?: string
}

export interface TaskUpdate {
  title?: string
  description?: string
  completed?: boolean
}

export interface TaskFilters {
  status?: 'all' | 'pending' | 'completed'
  sort?: 'created_at' | 'updated_at' | 'title'
  order?: 'asc' | 'desc'
}
