/**
 * EditTaskForm Component
 * Form for editing existing tasks
 * Based on specs/ui/task-management-ui.md
 */

"use client"

import * as React from "react"
import { Task, TaskUpdate } from "@/types/task"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert } from "@/components/ui/alert"

export interface EditTaskFormProps {
  task: Task
  onSubmit: (taskId: number, updates: TaskUpdate) => Promise<void>
  onCancel?: () => void
  onDelete?: () => void
}

export function EditTaskForm({
  task,
  onSubmit,
  onCancel,
  onDelete,
}: EditTaskFormProps) {
  const [title, setTitle] = React.useState(task.title)
  const [description, setDescription] = React.useState(task.description || "")
  const [error, setError] = React.useState("")
  const [loading, setLoading] = React.useState(false)

  const hasChanges =
    title.trim() !== task.title ||
    description.trim() !== (task.description || "")

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

      await onSubmit(task.id, updates)
    } catch (err: any) {
      setError(err.message || "Failed to update task")
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
