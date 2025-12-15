/**
 * TaskFilters Component
 * Filter tabs for All/Active/Completed tasks
 * Based on specs/ui/task-management-ui.md
 */

"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export type TaskFilter = "all" | "active" | "completed"

export interface TaskFiltersProps {
  activeFilter: TaskFilter
  onFilterChange: (filter: TaskFilter) => void
  taskCounts?: {
    all: number
    active: number
    completed: number
  }
}

export function TaskFilters({
  activeFilter,
  onFilterChange,
  taskCounts,
}: TaskFiltersProps) {
  const filters: { key: TaskFilter; label: string }[] = [
    { key: "all", label: "All" },
    { key: "active", label: "Active" },
    { key: "completed", label: "Completed" },
  ]

  return (
    <div className="flex flex-wrap gap-2 sm:gap-3 mb-6 sm:mb-8 p-1 bg-gray-100 rounded-xl border border-gray-200 w-full sm:w-fit">
      {filters.map((filter) => {
        const isActive = activeFilter === filter.key
        const count = taskCounts?.[filter.key] ?? 0

        return (
          <button
            key={filter.key}
            onClick={() => onFilterChange(filter.key)}
            className={cn(
              "relative flex-1 sm:flex-none px-4 sm:px-5 py-2 sm:py-2.5 text-xs sm:text-sm font-semibold rounded-lg transition-all duration-200 flex items-center justify-center gap-1.5 sm:gap-2 min-h-[44px]",
              isActive
                ? "bg-white text-blue-600 shadow-md shadow-blue-500/10"
                : "text-gray-600 hover:text-gray-900 hover:bg-white/50"
            )}
          >
            <span>{filter.label}</span>
            {taskCounts && (
              <span
                className={cn(
                  "min-w-[20px] sm:min-w-[24px] h-5 sm:h-6 px-1.5 sm:px-2 rounded-full text-xs font-bold flex items-center justify-center transition-all duration-200",
                  isActive
                    ? "bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-sm"
                    : "bg-gray-200 text-gray-600"
                )}
              >
                {count}
              </span>
            )}

            {/* Active indicator dot */}
            {isActive && (
              <div className="absolute bottom-0.5 sm:bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-blue-600 rounded-full" />
            )}
          </button>
        )
      })}
    </div>
  )
}
