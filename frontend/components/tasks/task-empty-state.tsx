/**
 * TaskEmptyState Component
 * Friendly message when no tasks match current filter
 * Based on specs/ui/task-management-ui.md
 */

import * as React from "react"
import { Button } from "@/components/ui/button"
import { PlusCircle, CheckCircle, Clipboard } from "lucide-react"

export interface TaskEmptyStateProps {
  filter?: "all" | "active" | "completed"
  onCreateTask?: () => void
}

export function TaskEmptyState({
  filter = "all",
  onCreateTask,
}: TaskEmptyStateProps) {
  const getContent = () => {
    switch (filter) {
      case "active":
        return {
          icon: <CheckCircle className="h-16 w-16 text-green-500" />,
          title: "All done!",
          description: "You have no active tasks.",
          showButton: false,
        }
      case "completed":
        return {
          icon: <Clipboard className="h-16 w-16 text-gray-400" />,
          title: "No completed tasks yet",
          description: "Complete a task to see it here.",
          showButton: false,
        }
      default:
        return {
          icon: <PlusCircle className="h-16 w-16 text-blue-500" />,
          title: "No tasks yet!",
          description: "Create your first task to get started.",
          showButton: true,
        }
    }
  }

  const content = getContent()

  return (
    <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
      <div className="p-6 bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl mb-6 shadow-lg">
        {content.icon}
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-3">
        {content.title}
      </h3>
      <p className="text-base text-gray-600 mb-8 max-w-md leading-relaxed">
        {content.description}
      </p>
      {content.showButton && onCreateTask && (
        <Button
          onClick={onCreateTask}
          icon={<PlusCircle className="h-5 w-5" />}
          size="large"
          className="shadow-xl shadow-blue-500/30"
        >
          Create Your First Task
        </Button>
      )}
    </div>
  )
}
