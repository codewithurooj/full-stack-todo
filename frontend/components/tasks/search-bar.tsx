/**
 * SearchBar Component
 * Search input with debounce for filtering tasks by title/description
 * Based on specs/009-intermediate-features/spec.md - US4
 */

"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Search, X } from "lucide-react"

export interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  debounceMs?: number
  resultCount?: number
  className?: string
}

export function SearchBar({
  value,
  onChange,
  placeholder = "Search tasks...",
  debounceMs = 300,
  resultCount,
  className,
}: SearchBarProps) {
  const [inputValue, setInputValue] = React.useState(value)
  const debounceTimerRef = React.useRef<NodeJS.Timeout | null>(null)

  // Sync inputValue with prop value when it changes externally
  React.useEffect(() => {
    setInputValue(value)
  }, [value])

  // Debounce the onChange callback
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    setInputValue(newValue)

    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    // Set new timer
    debounceTimerRef.current = setTimeout(() => {
      onChange(newValue)
    }, debounceMs)
  }

  // Clear search
  const handleClear = () => {
    setInputValue('')
    onChange('')
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }
  }

  // Cleanup timer on unmount
  React.useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [])

  return (
    <div className={cn("relative", className)}>
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-gray-400" />
        </div>

        <input
          type="text"
          value={inputValue}
          onChange={handleInputChange}
          placeholder={placeholder}
          className={cn(
            "w-full pl-10 pr-10 py-2.5 border border-gray-300 rounded-lg",
            "focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent",
            "transition-all duration-200",
            "text-sm placeholder:text-gray-400"
          )}
        />

        {inputValue && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute inset-y-0 right-0 pr-3 flex items-center hover:text-gray-700 text-gray-400 transition-colors"
            aria-label="Clear search"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Result count indicator */}
      {value && resultCount !== undefined && (
        <div className="mt-2 text-xs text-gray-600">
          {resultCount === 0 ? (
            <span className="text-orange-600">No tasks found</span>
          ) : (
            <span>
              Found {resultCount} {resultCount === 1 ? 'task' : 'tasks'}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
