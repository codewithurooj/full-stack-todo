/**
 * TaskList Component
 * Container that displays all tasks with filtering
 * Based on specs/ui/task-management-ui.md
 */

"use client"

import * as React from "react"
import { Task } from "@/types/task"
import { TaskItem } from "./task-item"
import { TaskEmptyState } from "./task-empty-state"

export interface TaskListProps {
  tasks: Task[]
  onTaskClick?: (task: Task) => void
  onTaskComplete?: (taskId: number) => void
  onTaskEdit?: (task: Task) => void
  onTaskDelete?: (taskId: number) => void
  loading?: boolean
  emptyMessage?: string
  filter?: "all" | "active" | "completed"
}

export function TaskList({
  tasks,
  onTaskClick,
  onTaskComplete,
  onTaskEdit,
  onTaskDelete,
  loading = false,
  filter = "all",
}: TaskListProps) {
  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="relative p-5 rounded-xl border-2 border-gray-200 bg-white overflow-hidden"
          >
            {/* Shimmer effect */}
            <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/60 to-transparent" />

            <div className="flex items-start gap-4">
              <div className="h-5 w-5 bg-gray-200 rounded animate-pulse" />
              <div className="flex-1 space-y-3">
                <div className="h-5 bg-gray-200 rounded-md w-3/4 animate-pulse" />
                <div className="h-4 bg-gray-200 rounded-md w-full animate-pulse" />
                <div className="h-3 bg-gray-200 rounded-md w-1/4 animate-pulse" />
              </div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (tasks.length === 0) {
    return <TaskEmptyState filter={filter} />
  }

  return (
    <div className="space-y-4">
      {tasks.map((task, index) => (
        <div
          key={task.id}
          className="animate-in fade-in slide-in-from-bottom-2 duration-300"
          style={{ animationDelay: `${index * 50}ms` }}
        >
          <TaskItem
            task={task}
            onComplete={onTaskComplete}
            onEdit={() => onTaskEdit?.(task)}
            onDelete={() => onTaskDelete?.(task.id)}
            variant="list"
          />
        </div>
      ))}
    </div>
  )
}
