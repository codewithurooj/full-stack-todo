/**
 * TagList Component
 * Displays a list of task tags as badges
 * Based on specs/009-intermediate-features/spec.md - US2
 */

"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { X } from "lucide-react"

export interface TagListProps {
  tags: string[]
  onRemove?: (tag: string) => void
  className?: string
  size?: 'small' | 'medium'
  maxDisplay?: number
}

const SIZE_STYLES = {
  small: 'px-2 py-0.5 text-xs',
  medium: 'px-2.5 py-1 text-sm',
}

export function TagList({
  tags,
  onRemove,
  className,
  size = 'medium',
  maxDisplay
}: TagListProps) {
  if (!tags || tags.length === 0) {
    return null
  }

  const displayTags = maxDisplay ? tags.slice(0, maxDisplay) : tags
  const remainingCount = maxDisplay && tags.length > maxDisplay ? tags.length - maxDisplay : 0

  return (
    <div className={cn("flex flex-wrap gap-1.5", className)}>
      {displayTags.map((tag, index) => (
        <span
          key={`${tag}-${index}`}
          className={cn(
            "inline-flex items-center gap-1 font-medium rounded-md bg-blue-100 text-blue-800 border border-blue-300 transition-all duration-200 hover:bg-blue-200",
            SIZE_STYLES[size]
          )}
        >
          {tag}
          {onRemove && (
            <button
              type="button"
              onClick={() => onRemove(tag)}
              className="ml-0.5 hover:text-blue-900 focus:outline-none"
              aria-label={`Remove ${tag} tag`}
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </span>
      ))}
      {remainingCount > 0 && (
        <span
          className={cn(
            "inline-flex items-center font-medium rounded-md bg-gray-100 text-gray-600 border border-gray-300",
            SIZE_STYLES[size]
          )}
        >
          +{remainingCount}
        </span>
      )}
    </div>
  )
}
