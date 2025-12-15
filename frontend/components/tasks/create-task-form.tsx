/**
 * CreateTaskForm Component
 * Form for creating new tasks
 * Based on specs/ui/task-management-ui.md
 */

"use client"

import * as React from "react"
import { TaskCreate } from "@/types/task"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert } from "@/components/ui/alert"

export interface CreateTaskFormProps {
  onSubmit: (taskData: TaskCreate) => Promise<void>
  onCancel?: () => void
}

export function CreateTaskForm({ onSubmit, onCancel }: CreateTaskFormProps) {
  const [title, setTitle] = React.useState("")
  const [description, setDescription] = React.useState("")
  const [error, setError] = React.useState("")
  const [loading, setLoading] = React.useState(false)

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
      await onSubmit({
        title: trimmedTitle,
        description: description.trim() || undefined,
      })

      // Reset form on success
      setTitle("")
      setDescription("")
    } catch (err: any) {
      setError(err.message || "Failed to create task")
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
