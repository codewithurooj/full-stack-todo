/**
 * AdvancedTaskFilters Component
 * Comprehensive filtering panel for priority, tags, status, and date range
 * Based on specs/009-intermediate-features/spec.md - US3
 */

"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { X, Filter } from "lucide-react"
import { Button } from "@/components/ui/button"

export interface AdvancedFilterValues {
  priority?: 'high' | 'medium' | 'low'
  tags?: string[]
  status?: 'all' | 'pending' | 'completed'
  dateFrom?: string
  dateTo?: string
}

export interface AdvancedTaskFiltersProps {
  filters: AdvancedFilterValues
  onFilterChange: (filters: AdvancedFilterValues) => void
  availableTags: string[]
  className?: string
}

export function AdvancedTaskFilters({
  filters,
  onFilterChange,
  availableTags,
  className,
}: AdvancedTaskFiltersProps) {
  const [isExpanded, setIsExpanded] = React.useState(false)

  const handlePriorityChange = (priority: 'high' | 'medium' | 'low' | undefined) => {
    onFilterChange({ ...filters, priority })
  }

  const handleStatusChange = (status: 'all' | 'pending' | 'completed') => {
    onFilterChange({ ...filters, status })
  }

  const handleTagToggle = (tag: string) => {
    const currentTags = filters.tags || []
    const newTags = currentTags.includes(tag)
      ? currentTags.filter(t => t !== tag)
      : [...currentTags, tag]
    onFilterChange({ ...filters, tags: newTags.length > 0 ? newTags : undefined })
  }

  const handleDateFromChange = (dateFrom: string) => {
    onFilterChange({ ...filters, dateFrom: dateFrom || undefined })
  }

  const handleDateToChange = (dateTo: string) => {
    onFilterChange({ ...filters, dateTo: dateTo || undefined })
  }

  const clearAllFilters = () => {
    onFilterChange({})
    setIsExpanded(false)
  }

  const activeFilterCount = [
    filters.priority,
    filters.tags?.length,
    filters.status !== 'all' && filters.status,
    filters.dateFrom,
    filters.dateTo,
  ].filter(Boolean).length

  return (
    <div className={cn("space-y-4", className)}>
      {/* Filter toggle button */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className={cn(
            "flex items-center gap-2 px-4 py-2 rounded-lg border transition-all duration-200",
            isExpanded
              ? "bg-blue-50 border-blue-300 text-blue-700"
              : "bg-white border-gray-300 text-gray-700 hover:bg-gray-50"
          )}
        >
          <Filter className="h-4 w-4" />
          <span className="font-medium text-sm">Filters</span>
          {activeFilterCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-bold bg-blue-600 text-white rounded-full">
              {activeFilterCount}
            </span>
          )}
        </button>

        {activeFilterCount > 0 && (
          <button
            type="button"
            onClick={clearAllFilters}
            className="text-sm text-gray-600 hover:text-gray-900 underline transition-colors"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Expanded filter panel */}
      {isExpanded && (
        <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-4 animate-in slide-in-from-top-2">
          {/* Priority filter */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Priority
            </label>
            <div className="flex flex-wrap gap-2">
              {(['high', 'medium', 'low'] as const).map((priority) => (
                <button
                  key={priority}
                  type="button"
                  onClick={() =>
                    handlePriorityChange(filters.priority === priority ? undefined : priority)
                  }
                  className={cn(
                    "px-3 py-1.5 text-sm font-medium rounded-md border transition-all duration-200",
                    filters.priority === priority
                      ? priority === 'high'
                        ? "bg-red-100 text-red-800 border-red-300"
                        : priority === 'medium'
                        ? "bg-yellow-100 text-yellow-800 border-yellow-300"
                        : "bg-green-100 text-green-800 border-green-300"
                      : "bg-white text-gray-700 border-gray-300 hover:bg-gray-100"
                  )}
                >
                  {priority.charAt(0).toUpperCase() + priority.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Status filter */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Status
            </label>
            <div className="flex flex-wrap gap-2">
              {(['all', 'pending', 'completed'] as const).map((status) => (
                <button
                  key={status}
                  type="button"
                  onClick={() => handleStatusChange(status)}
                  className={cn(
                    "px-3 py-1.5 text-sm font-medium rounded-md border transition-all duration-200",
                    filters.status === status || (!filters.status && status === 'all')
                      ? "bg-blue-100 text-blue-800 border-blue-300"
                      : "bg-white text-gray-700 border-gray-300 hover:bg-gray-100"
                  )}
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Tags filter */}
          {availableTags.length > 0 && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Tags
              </label>
              <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                {availableTags.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => handleTagToggle(tag)}
                    className={cn(
                      "px-3 py-1.5 text-sm font-medium rounded-md border transition-all duration-200",
                      filters.tags?.includes(tag)
                        ? "bg-blue-100 text-blue-800 border-blue-300"
                        : "bg-white text-gray-700 border-gray-300 hover:bg-gray-100"
                    )}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Date range filter */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Date Range
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label htmlFor="date-from" className="block text-xs text-gray-600 mb-1">
                  From
                </label>
                <input
                  id="date-from"
                  type="date"
                  value={filters.dateFrom || ''}
                  onChange={(e) => handleDateFromChange(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                />
              </div>
              <div>
                <label htmlFor="date-to" className="block text-xs text-gray-600 mb-1">
                  To
                </label>
                <input
                  id="date-to"
                  type="date"
                  value={filters.dateTo || ''}
                  onChange={(e) => handleDateToChange(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          {/* Clear filters button */}
          {activeFilterCount > 0 && (
            <div className="pt-2 border-t border-gray-200">
              <Button
                type="button"
                variant="secondary"
                size="small"
                onClick={clearAllFilters}
                icon={<X className="h-4 w-4" />}
                className="w-full"
              >
                Clear All Filters
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
