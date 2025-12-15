/**
 * DeleteTaskConfirmation Component
 * Confirmation dialog before deleting a task
 * Based on specs/ui/task-management-ui.md
 */

"use client"

import * as React from "react"
import { Task } from "@/types/task"
import { Button } from "@/components/ui/button"
import { Alert } from "@/components/ui/alert"
import { AlertTriangle } from "lucide-react"

export interface DeleteTaskConfirmationProps {
  task: Task
  onConfirm: (taskId: number) => Promise<void>
  onCancel: () => void
}

export function DeleteTaskConfirmation({
  task,
  onConfirm,
  onCancel,
}: DeleteTaskConfirmationProps) {
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState("")

  const handleConfirm = async () => {
    setError("")
    setLoading(true)

    try {
      await onConfirm(task.id)
      onCancel() // Close modal on success
    } catch (err: any) {
      setError(err.message || "Failed to delete task")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center gap-3 mb-4">
        <AlertTriangle className="h-6 w-6 text-red-600" />
        <h2 className="text-xl font-semibold text-gray-900">Delete Task?</h2>
      </div>

      {error && (
        <Alert
          variant="error"
          message={error}
          dismissible
          onClose={() => setError("")}
          className="mb-4"
        />
      )}

      <p className="text-gray-700 mb-4">
        Are you sure you want to delete this task? This action cannot be undone.
      </p>

      <div className="bg-gray-50 p-3 rounded-md mb-6">
        <p className="font-medium text-gray-900">{task.title}</p>
        {task.description && (
          <p className="text-sm text-gray-600 mt-1">{task.description}</p>
        )}
      </div>

      <div className="flex gap-3 justify-end">
        <Button
          variant="secondary"
          onClick={onCancel}
          disabled={loading}
        >
          Cancel
        </Button>
        <Button
          variant="danger"
          onClick={handleConfirm}
          loading={loading}
        >
          Delete Task
        </Button>
      </div>
    </div>
  )
}
