/**
 * TaskItem Component
 * Individual task row displaying task information and actions
 * Based on specs/ui/task-management-ui.md
 */

"use client"

import * as React from "react"
import { Task } from "@/types/task"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Pencil, Trash2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { formatDistanceToNow } from "date-fns"

export interface TaskItemProps {
  task: Task
  onComplete?: (taskId: number) => void
  onEdit?: () => void
  onDelete?: () => void
  variant?: "list" | "card"
  showActions?: boolean
}

export function TaskItem({
  task,
  onComplete,
  onEdit,
  onDelete,
  variant = "list",
  showActions = true,
}: TaskItemProps) {
  const [isHovered, setIsHovered] = React.useState(false)

  const handleCheckboxChange = () => {
    if (onComplete) {
      onComplete(task.id)
    }
  }

  const getRelativeTime = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true })
    } catch {
      return dateString
    }
  }

  if (variant === "card") {
    return (
      <div
        className={cn(
          "group relative p-4 sm:p-6 rounded-xl border-2 bg-white transition-all duration-300",
          task.completed
            ? "border-gray-200 bg-gradient-to-br from-gray-50 to-gray-100/50"
            : "border-gray-200 hover:border-blue-300 hover:shadow-lg hover:shadow-blue-100/50",
          "hover:-translate-y-0.5"
        )}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Priority indicator bar */}
        <div className={cn(
          "absolute left-0 top-0 bottom-0 w-1 rounded-l-xl transition-all duration-300",
          !task.completed && "bg-gradient-to-b from-blue-500 to-blue-600",
          task.completed && "bg-gray-300"
        )} />

        <div className="flex items-start gap-3 sm:gap-4 mb-3 sm:mb-4">
          <Checkbox
            checked={task.completed}
            onCheckedChange={handleCheckboxChange}
            className="mt-1 transition-transform duration-200 hover:scale-110 min-w-[20px] min-h-[20px]"
          />
          <div className="flex-1 min-w-0">
            <h3
              className={cn(
                "font-semibold text-base sm:text-lg transition-all duration-300 break-words",
                task.completed
                  ? "line-through text-gray-500"
                  : "text-gray-900 group-hover:text-blue-700"
              )}
            >
              {task.title}
            </h3>
          </div>
        </div>

        {task.description && (
          <p className={cn(
            "text-sm ml-8 sm:ml-11 mb-3 sm:mb-4 leading-relaxed transition-colors duration-200 break-words",
            task.completed ? "text-gray-400" : "text-gray-600"
          )}>
            {task.description}
          </p>
        )}

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 ml-8 sm:ml-11">
          <span className="text-xs text-gray-500 font-medium">
            Created {getRelativeTime(task.created_at)}
          </span>

          {showActions && (
            <div className={cn(
              "flex gap-2 transition-all duration-300",
              "sm:opacity-0 sm:-translate-x-2",
              isHovered && "sm:opacity-100 sm:translate-x-0"
            )}>
              <Button
                variant="ghost"
                size="small"
                onClick={onEdit}
                icon={<Pencil className="h-4 w-4" />}
                className="hover:bg-blue-50 hover:text-blue-600 flex-1 sm:flex-none min-h-[44px]"
              >
                Edit
              </Button>
              <Button
                variant="ghost"
                size="small"
                onClick={onDelete}
                icon={<Trash2 className="h-4 w-4" />}
                className="hover:bg-red-50 hover:text-red-600 flex-1 sm:flex-none min-h-[44px]"
              >
                Delete
              </Button>
            </div>
          )}
        </div>
      </div>
    )
  }

  // List variant (default)
  return (
    <div
      className={cn(
        "group relative p-4 sm:p-5 rounded-xl border-2 bg-white transition-all duration-300",
        task.completed
          ? "border-gray-200 bg-gradient-to-r from-gray-50 to-white"
          : "border-gray-200 hover:border-blue-300 hover:shadow-lg hover:shadow-blue-100/50",
        "hover:-translate-y-0.5"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Priority indicator bar */}
      <div className={cn(
        "absolute left-0 top-0 bottom-0 w-1 rounded-l-xl transition-all duration-300",
        !task.completed && "bg-gradient-to-b from-blue-500 to-blue-600",
        task.completed && "bg-gray-300"
      )} />

      <div className="flex items-start gap-3 sm:gap-4">
        <Checkbox
          checked={task.completed}
          onCheckedChange={handleCheckboxChange}
          className="mt-1 transition-transform duration-200 hover:scale-110 min-w-[20px] min-h-[20px]"
        />

        <div className="flex-1 min-w-0">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 sm:gap-4">
            <div className="flex-1 min-w-0">
              <h3
                className={cn(
                  "font-semibold text-base mb-2 transition-all duration-300 break-words",
                  task.completed
                    ? "line-through text-gray-500"
                    : "text-gray-900 group-hover:text-blue-700"
                )}
              >
                {task.title}
              </h3>

              {task.description && (
                <p className={cn(
                  "text-sm mb-3 leading-relaxed transition-colors duration-200 break-words",
                  task.completed ? "text-gray-400" : "text-gray-600"
                )}>
                  {task.description}
                </p>
              )}

              <span className="text-xs text-gray-500 font-medium">
                Created {getRelativeTime(task.created_at)}
              </span>
            </div>

            {showActions && (
              <div className={cn(
                "flex gap-2 flex-shrink-0 transition-all duration-300 w-full sm:w-auto",
                "sm:opacity-0 sm:-translate-x-2",
                isHovered && "sm:opacity-100 sm:translate-x-0"
              )}>
                <Button
                  variant="ghost"
                  size="small"
                  onClick={onEdit}
                  icon={<Pencil className="h-4 w-4" />}
                  className="hover:bg-blue-50 hover:text-blue-600 flex-1 sm:flex-none min-h-[44px]"
                >
                  Edit
                </Button>
                <Button
                  variant="ghost"
                  size="small"
                  onClick={onDelete}
                  icon={<Trash2 className="h-4 w-4" />}
                  className="hover:bg-red-50 hover:text-red-600 flex-1 sm:flex-none min-h-[44px]"
                >
                  Delete
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
