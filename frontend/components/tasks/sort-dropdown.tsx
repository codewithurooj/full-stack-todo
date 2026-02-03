/**
 * SortDropdown Component
 * Dropdown for sorting tasks by various criteria with order toggle
 * Based on specs/009-intermediate-features/spec.md - US5
 */

"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react"

export interface SortDropdownProps {
  sortBy: string
  sortOrder: 'asc' | 'desc'
  onSortChange: (sortBy: string, sortOrder: 'asc' | 'desc') => void
  className?: string
}

const SORT_OPTIONS = [
  { value: 'created_at', label: 'Created Date' },
  { value: 'updated_at', label: 'Updated Date' },
  { value: 'title', label: 'Title' },
  { value: 'priority', label: 'Priority' },
  { value: 'due_date', label: 'Due Date' },
]

export function SortDropdown({
  sortBy,
  sortOrder,
  onSortChange,
  className,
}: SortDropdownProps) {
  const [isOpen, setIsOpen] = React.useState(false)
  const dropdownRef = React.useRef<HTMLDivElement>(null)

  const currentLabel = SORT_OPTIONS.find(opt => opt.value === sortBy)?.label || 'Sort'

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSortByChange = (value: string) => {
    onSortChange(value, sortOrder)
    setIsOpen(false)
  }

  const toggleSortOrder = (e: React.MouseEvent) => {
    e.stopPropagation()
    onSortChange(sortBy, sortOrder === 'asc' ? 'desc' : 'asc')
  }

  return (
    <div ref={dropdownRef} className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-2 px-4 py-2.5 border border-gray-300 rounded-lg bg-white",
          "hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent",
          "transition-all duration-200 text-sm font-medium text-gray-700",
          "min-w-[160px]"
        )}
      >
        <ArrowUpDown className="h-4 w-4 text-gray-500" />
        <span className="flex-1 text-left">{currentLabel}</span>
        <button
          type="button"
          onClick={toggleSortOrder}
          className="p-0.5 hover:bg-gray-200 rounded transition-colors"
          aria-label={`Sort order: ${sortOrder === 'asc' ? 'ascending' : 'descending'}`}
        >
          {sortOrder === 'asc' ? (
            <ArrowUp className="h-4 w-4 text-blue-600" />
          ) : (
            <ArrowDown className="h-4 w-4 text-blue-600" />
          )}
        </button>
      </button>

      {/* Dropdown menu */}
      {isOpen && (
        <div className="absolute z-10 mt-2 w-full bg-white border border-gray-300 rounded-lg shadow-lg overflow-hidden">
          {SORT_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => handleSortByChange(option.value)}
              className={cn(
                "w-full px-4 py-2.5 text-left text-sm hover:bg-blue-50 transition-colors",
                sortBy === option.value && "bg-blue-100 text-blue-700 font-medium"
              )}
            >
              {option.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
