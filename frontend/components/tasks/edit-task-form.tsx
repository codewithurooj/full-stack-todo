/**
 * EditTaskForm Component
 * Form for editing existing tasks with recurring pattern support
 * Based on specs/ui/task-management-ui.md and specs/010-recurring-due-dates/spec.md
 */

"use client"

import * as React from "react"
import { Task, TaskUpdate } from "@/types/task"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert } from "@/components/ui/alert"
import { TagInput } from "./tag-input"
import { RecurrenceEditor } from "./recurrence-editor"
import { RecurringPattern } from "@/hooks/useRecurring"
import { recurringApi } from "@/lib/api/recurring"
import { ApiError } from "@/lib/api/client"

export interface EditTaskFormProps {
  userId?: string
  task: Task
  onSubmit: (taskId: number, updates: TaskUpdate) => Promise<void>
  onCancel?: () => void
  onDelete?: () => void
  availableTags?: string[]
  onRecurringChange?: () => void
}

export function EditTaskForm({
  userId,
  task,
  onSubmit,
  onCancel,
  onDelete,
  availableTags = [],
  onRecurringChange,
}: EditTaskFormProps) {
  const [title, setTitle] = React.useState(task.title)
  const [description, setDescription] = React.useState(task.description || "")
  const [priority, setPriority] = React.useState<'high' | 'medium' | 'low'>(task.priority)
  const [tags, setTags] = React.useState<string[]>(task.tags || [])
  const [dueDate, setDueDate] = React.useState<string>(() => {
    // Convert backend ISO format to datetime-local format
    if (task.due_date) {
      const date = new Date(task.due_date)
      return date.toISOString().slice(0, 16)
    }
    return ""
  })
  const [error, setError] = React.useState("")
  const [loading, setLoading] = React.useState(false)

  const hasChanges =
    title.trim() !== task.title ||
    description.trim() !== (task.description || "") ||
    priority !== task.priority ||
    dueDate !== (task.due_date ? new Date(task.due_date).toISOString().slice(0, 16) : "") ||
    JSON.stringify(tags.sort()) !== JSON.stringify((task.tags || []).sort())

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

    setError("")
    setLoading(true)

    try {
      const updates: TaskUpdate = {}

      if (title.trim() !== task.title) {
        updates.title = trimmedTitle
      }

      const newDesc = description.trim()
      if (newDesc !== (task.description || "")) {
        updates.description = newDesc || undefined
      }

      if (priority !== task.priority) {
        updates.priority = priority
      }

      if (JSON.stringify(tags.sort()) !== JSON.stringify((task.tags || []).sort())) {
        updates.tags = tags
      }

      if (dueDate !== (task.due_date ? new Date(task.due_date).toISOString().slice(0, 16) : "")) {
        updates.due_date = dueDate ? new Date(dueDate).toISOString() : undefined
      }

      await onSubmit(task.id, updates)
    } catch (err: any) {
      // Extract detailed error message
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError(err.message || "Failed to update task")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h2 className="text-xl font-semibold mb-4">Edit Task</h2>

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
          Tags
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

      {userId && (
        <div className="border-t pt-4">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Recurring Pattern</h3>
          <RecurrenceEditor
            userId={userId}
            task={task}
            onSave={async () => {
              // Trigger parent refresh after recurring pattern saved
              onRecurringChange?.()
            }}
          />
        </div>
      )}

      <div className="flex gap-3 justify-between pt-2">
        {onDelete && (
          <Button
            type="button"
            variant="danger"
            onClick={onDelete}
            disabled={loading}
          >
            Delete Task
          </Button>
        )}
        <div className="flex gap-3">
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
          <Button
            type="submit"
            loading={loading}
            disabled={!title.trim() || !hasChanges}
          >
            Save Changes
          </Button>
        </div>
      </div>
    </form>
  )
}
