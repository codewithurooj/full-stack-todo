/**
 * EmptyState Component
 * Display when task list is empty or no search results
 */

import * as React from "react"
import { cn } from "@/lib/utils"
import { Inbox, Search, Filter, Tag } from "lucide-react"
import { Button } from "@/components/ui/button"

export interface EmptyStateProps {
  type: "no-tasks" | "no-search-results" | "no-filter-results" | "no-tags"
  onAction?: () => void
  actionLabel?: string
  className?: string
}

const emptyStateConfig = {
  "no-tasks": {
    icon: Inbox,
    title: "No tasks yet",
    description: "Get started by creating your first task",
    iconColor: "text-blue-500",
  },
  "no-search-results": {
    icon: Search,
    title: "No results found",
    description: "Try adjusting your search terms or filters",
    iconColor: "text-gray-400",
  },
  "no-filter-results": {
    icon: Filter,
    title: "No tasks match your filters",
    description: "Try removing some filters to see more tasks",
    iconColor: "text-orange-500",
  },
  "no-tags": {
    icon: Tag,
    title: "No tags available",
    description: "Create tasks with tags to organize them",
    iconColor: "text-purple-500",
  },
}

export function EmptyState({
  type,
  onAction,
  actionLabel,
  className,
}: EmptyStateProps) {
  const config = emptyStateConfig[type]
  const Icon = config.icon

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-16 px-4 text-center",
        className
      )}
    >
      <div
        className={cn(
          "rounded-full bg-gray-100 p-6 mb-6",
          "transition-transform hover:scale-105 duration-300"
        )}
      >
        <Icon className={cn("h-16 w-16", config.iconColor)} />
      </div>

      <h3 className="text-xl font-semibold text-gray-900 mb-2">
        {config.title}
      </h3>

      <p className="text-gray-600 mb-6 max-w-md">{config.description}</p>

      {onAction && actionLabel && (
        <Button onClick={onAction} variant="primary">
          {actionLabel}
        </Button>
      )}

      {type === "no-search-results" && (
        <div className="mt-8 text-xs text-gray-500 space-y-1">
          <p>Search tips:</p>
          <ul className="list-disc list-inside text-left inline-block">
            <li>Check for typos</li>
            <li>Try different keywords</li>
            <li>Use fewer filters</li>
          </ul>
        </div>
      )}

      {type === "no-filter-results" && (
        <div className="mt-8 text-xs text-gray-500">
          <p>Current filters may be too restrictive</p>
        </div>
      )}
    </div>
  )
}
