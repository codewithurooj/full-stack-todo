/**
 * CreateTaskForm Component
 * Form for creating new tasks with recurring pattern support
 * Based on specs/ui/task-management-ui.md and specs/010-recurring-due-dates/spec.md
 */

"use client"

import * as React from "react"
import { TaskCreate } from "@/types/task"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert } from "@/components/ui/alert"
import { TagInput } from "./tag-input"
import { RecurringTaskForm } from "./recurring-task-form"
import { RecurringPattern } from "@/hooks/useRecurring"
import { recurringApi } from "@/lib/api/recurring"
import { ApiError } from "@/lib/api/client"

export interface CreateTaskFormProps {
  userId?: string
  onSubmit: (taskData: TaskCreate) => Promise<{ id: number }>
  onCancel?: () => void
  availableTags?: string[]
}

export function CreateTaskForm({ userId, onSubmit, onCancel, availableTags = [] }: CreateTaskFormProps) {
  const [title, setTitle] = React.useState("")
  const [description, setDescription] = React.useState("")
  const [priority, setPriority] = React.useState<'high' | 'medium' | 'low'>('medium')
  const [tags, setTags] = React.useState<string[]>([])
  const [dueDate, setDueDate] = React.useState<string>("")
  const [recurringPattern, setRecurringPattern] = React.useState<RecurringPattern>(null)
  const [recurringInterval, setRecurringInterval] = React.useState<number>(1)
  const [recurringDays, setRecurringDays] = React.useState<string[] | null>(null)
  const [recurringEndDate, setRecurringEndDate] = React.useState<string | null>(null)
  const [error, setError] = React.useState("")
  const [loading, setLoading] = React.useState(false)

  // Handle recurring pattern changes from RecurringTaskForm
  const handleRecurringChange = React.useCallback(
    (pattern: RecurringPattern, interval: number, days: string[] | null, endDate: string | null) => {
      setRecurringPattern(pattern)
      setRecurringInterval(interval)
      setRecurringDays(days)
      setRecurringEndDate(endDate)
    },
    []
  )

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const trimmedTitle = title.trim()
    if (!trimmedTitle) {
      setError("Task title is required")
      return
    }

    if (trimmedTitle.length > 200) {
      setError("Title cannot exceed 200 characters")
      return
    }

    if (description.length > 1000) {
      setError("Description cannot exceed 1000 characters")
      return
    }

    // Client-side tag validation
    if (tags.length > 50) {
      setError("Maximum 50 tags allowed")
      return
    }

    for (const tag of tags) {
      if (tag.length > 50) {
        setError(`Tag '${tag}' exceeds maximum length of 50 characters`)
        return
      }
      if (!/^[\w-]+$/.test(tag)) {
        setError(`Tag '${tag}' contains invalid characters. Only alphanumeric, hyphens, and underscores allowed`)
        return
      }
    }

    // Validate recurring pattern requires due date
    if (recurringPattern && !dueDate) {
      setError("Due date is required for recurring tasks")
      return
    }

    // Validate weekly pattern requires days
    if (recurringPattern === 'weekly' && (!recurringDays || recurringDays.length === 0)) {
      setError("Please select at least one day for weekly recurring tasks")
      return
    }

    setError("")
    setLoading(true)

    try {
      // Step 1: Create the task
      const result = await onSubmit({
        title: trimmedTitle,
        description: description.trim() || undefined,
        priority,
        tags: tags.length > 0 ? tags : undefined,
        due_date: dueDate || undefined,
      })

      // Step 2: If recurring pattern is set, call recurring API
      if (recurringPattern && dueDate && result?.id && userId) {
        try {
          await recurringApi.setRecurring(
            userId,
            result.id,
            recurringPattern,
            recurringInterval,
            recurringDays || undefined,
            recurringEndDate || undefined
          )
        } catch (recurringErr) {
          console.error('Failed to set recurring pattern:', recurringErr)
          // Task was created but recurring failed - show warning
          setError("Task created but failed to set recurring pattern. Please edit the task to add recurring.")
          setLoading(false)
          return
        }
      }

      // Reset form on success
      setTitle("")
      setDescription("")
      setPriority('medium')
      setTags([])
      setDueDate("")
      setRecurringPattern(null)
      setRecurringInterval(1)
      setRecurringDays(null)
      setRecurringEndDate(null)
    } catch (err: any) {
      // Extract detailed error message
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError(err.message || "Failed to create task")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-xl font-semibold mb-4">Create New Task</h2>

      {error && (
        <Alert
          variant="error"
          message={error}
          dismissible
          onClose={() => setError("")}
        />
      )}

      <Input
        label="Title"
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="What needs to be done?"
        required
        autoFocus
        disabled={loading}
        maxLength={200}
        helperText={`${title.length}/200 characters`}
      />

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
          Description (Optional)
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Add more details... (optional)"
          rows={3}
          maxLength={1000}
          disabled={loading}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent disabled:opacity-50 resize-none"
        />
        <p className="mt-1 text-xs text-gray-600">{description.length}/1000 characters</p>
      </div>

      <div>
        <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-1">
          Priority
        </label>
        <select
          id="priority"
          value={priority}
          onChange={(e) => setPriority(e.target.value as 'high' | 'medium' | 'low')}
          disabled={loading}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent disabled:opacity-50"
        >
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Tags (Optional)
        </label>
        <TagInput
          value={tags}
          onChange={setTags}
          suggestions={availableTags}
          disabled={loading}
          placeholder="Add tags..."
        />
      </div>

      <div>
        <label htmlFor="due-date" className="block text-sm font-medium text-gray-700 mb-1">
          Due Date (Optional)
        </label>
        <Input
          id="due-date"
          type="datetime-local"
          value={dueDate}
          onChange={(e) => setDueDate(e.target.value)}
          disabled={loading}
        />
        <p className="text-xs text-gray-600 mt-1">
          Required for recurring tasks
        </p>
      </div>

      {dueDate && (
        <div className="border-t pt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Recurring Pattern</h3>
          <RecurringTaskForm
            userId={userId}
            initialPattern={recurringPattern}
            initialInterval={recurringInterval}
            initialDays={recurringDays}
            initialEndDate={recurringEndDate}
            onChange={handleRecurringChange}
            showAdvanced={true}
          />
        </div>
      )}

      <div className="flex gap-3 justify-end pt-2">
        {onCancel && (
          <Button
            type="button"
            variant="secondary"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </Button>
        )}
        <Button type="submit" loading={loading} disabled={!title.trim()}>
          Create Task
        </Button>
      </div>
    </form>
  )
}
