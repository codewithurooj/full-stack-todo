/**
 * TagInput Component
 * Input field with autocomplete for adding tags to tasks
 * Based on specs/009-intermediate-features/spec.md - US2
 */

"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { TagList } from "./tag-list"
import { Plus } from "lucide-react"

export interface TagInputProps {
  value: string[]
  onChange: (tags: string[]) => void
  suggestions?: string[]
  placeholder?: string
  maxTags?: number
  className?: string
  disabled?: boolean
}

export function TagInput({
  value,
  onChange,
  suggestions = [],
  placeholder = "Add tags...",
  maxTags = 50,
  className,
  disabled = false,
}: TagInputProps) {
  const [input, setInput] = React.useState('')
  const [filteredSuggestions, setFilteredSuggestions] = React.useState<string[]>([])
  const [showSuggestions, setShowSuggestions] = React.useState(false)
  const [selectedIndex, setSelectedIndex] = React.useState(-1)
  const inputRef = React.useRef<HTMLInputElement>(null)
  const suggestionsRef = React.useRef<HTMLDivElement>(null)

  // Filter suggestions based on input
  React.useEffect(() => {
    if (input.length > 0) {
      const filtered = suggestions
        .filter(s =>
          s.toLowerCase().includes(input.toLowerCase()) &&
          !value.includes(s)
        )
        .slice(0, 10) // Limit to 10 suggestions
      setFilteredSuggestions(filtered)
      setShowSuggestions(filtered.length > 0)
      setSelectedIndex(-1)
    } else {
      setFilteredSuggestions([])
      setShowSuggestions(false)
    }
  }, [input, suggestions, value])

  const addTag = (tag: string) => {
    const trimmedTag = tag.trim()
    if (
      trimmedTag &&
      !value.includes(trimmedTag) &&
      value.length < maxTags &&
      /^[\w-]+$/.test(trimmedTag) // Alphanumeric, hyphens, underscores only
    ) {
      onChange([...value, trimmedTag])
      setInput('')
      setShowSuggestions(false)
      setSelectedIndex(-1)
    }
  }

  const removeTag = (tag: string) => {
    onChange(value.filter(t => t !== tag))
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && input) {
      e.preventDefault()
      if (selectedIndex >= 0 && filteredSuggestions[selectedIndex]) {
        addTag(filteredSuggestions[selectedIndex])
      } else {
        addTag(input)
      }
    } else if (e.key === 'Backspace' && !input && value.length > 0) {
      // Remove last tag on backspace when input is empty
      removeTag(value[value.length - 1])
    } else if (e.key === 'ArrowDown' && showSuggestions) {
      e.preventDefault()
      setSelectedIndex(prev =>
        prev < filteredSuggestions.length - 1 ? prev + 1 : prev
      )
    } else if (e.key === 'ArrowUp' && showSuggestions) {
      e.preventDefault()
      setSelectedIndex(prev => (prev > 0 ? prev - 1 : -1))
    } else if (e.key === 'Escape') {
      setShowSuggestions(false)
      setSelectedIndex(-1)
    }
  }

  // Close suggestions when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className={cn("space-y-2", className)}>
      <div className="relative">
        <div
          className={cn(
            "flex flex-wrap gap-1.5 min-h-[42px] p-2 border rounded-md bg-white focus-within:ring-2 focus-within:ring-blue-600 focus-within:border-transparent transition-all",
            disabled ? "opacity-50 cursor-not-allowed bg-gray-50" : "border-gray-300"
          )}
        >
          <TagList tags={value} onRemove={disabled ? undefined : removeTag} size="small" />

          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => input && setShowSuggestions(filteredSuggestions.length > 0)}
            placeholder={value.length === 0 ? placeholder : ''}
            disabled={disabled || value.length >= maxTags}
            className="flex-1 min-w-[120px] px-2 py-1 text-sm outline-none disabled:cursor-not-allowed bg-transparent"
          />
        </div>

        {/* Autocomplete suggestions dropdown */}
        {showSuggestions && filteredSuggestions.length > 0 && (
          <div
            ref={suggestionsRef}
            className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-48 overflow-y-auto"
          >
            {filteredSuggestions.map((suggestion, index) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => addTag(suggestion)}
                className={cn(
                  "w-full px-3 py-2 text-left text-sm hover:bg-blue-50 transition-colors",
                  selectedIndex === index && "bg-blue-100"
                )}
              >
                <div className="flex items-center gap-2">
                  <Plus className="h-4 w-4 text-blue-600" />
                  {suggestion}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {value.length >= maxTags && (
        <p className="text-xs text-orange-600">
          Maximum of {maxTags} tags reached
        </p>
      )}

      <p className="text-xs text-gray-600">
        Press Enter to add a tag. Use alphanumeric characters, hyphens, and underscores only.
      </p>
    </div>
  )
}
