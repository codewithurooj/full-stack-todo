/**
 * RecurrenceDisplay Component
 * Visual display for recurring task patterns
 * Based on specs/010-recurring-due-dates/spec.md - T093
 */

"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import {
  formatRecurringPattern,
  getRecurringIcon,
  formatEndDate
} from "@/lib/rrule-parser"
import { LucideIcon } from "lucide-react"

export interface RecurrenceDisplayProps {
  pattern: string
  interval?: number
  days?: string[] | null
  endDate?: string | null
  nextOccurrence?: string | null
  className?: string
  size?: 'small' | 'medium'
  showIcon?: boolean
  showEndDate?: boolean
  showNextOccurrence?: boolean
}

const SIZE_STYLES = {
  small: 'px-2 py-0.5 text-xs',
  medium: 'px-2.5 py-1 text-sm',
}

const ICON_SIZE = {
  small: 12,
  medium: 14,
}

export function RecurrenceDisplay({
  pattern,
  interval = 1,
  days = null,
  endDate = null,
  nextOccurrence = null,
  className,
  size = 'medium',
  showIcon = true,
  showEndDate = false,
  showNextOccurrence = false,
}: RecurrenceDisplayProps) {
  // Get formatted text and icon
  const patternText = formatRecurringPattern(pattern, interval, days || undefined)
  const Icon: LucideIcon = getRecurringIcon(pattern)
  const iconSize = ICON_SIZE[size]

  // Don't render if no pattern
  if (!pattern || pattern === 'none') {
    return null
  }

  return (
    <div className={cn("inline-flex flex-col gap-1", className)}>
      {/* Main recurring badge */}
      <span
        className={cn(
          "inline-flex items-center gap-1.5 font-medium rounded-md border transition-all duration-200",
          "bg-blue-50 text-blue-800 border-blue-300",
          SIZE_STYLES[size]
        )}
      >
        {showIcon && <Icon size={iconSize} className="flex-shrink-0" />}
        <span>{patternText}</span>
      </span>

      {/* Optional: End date */}
      {showEndDate && endDate && (
        <span className="text-xs text-muted-foreground">
          Until {formatEndDate(endDate)}
        </span>
      )}

      {/* Optional: Next occurrence */}
      {showNextOccurrence && nextOccurrence && (
        <span className="text-xs text-muted-foreground">
          Next: {formatNextOccurrence(nextOccurrence)}
        </span>
      )}
    </div>
  )
}

/**
 * Format next occurrence date for display
 */
function formatNextOccurrence(isoDate: string): string {
  try {
    const date = new Date(isoDate)
    const now = new Date()
    const diffMs = date.getTime() - now.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    // Format based on proximity
    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Tomorrow'
    if (diffDays < 7) return date.toLocaleDateString('en-US', { weekday: 'long' })

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch (error) {
    return isoDate
  }
}

/**
 * Compact version for inline display (no icon, smaller)
 */
export function RecurrenceDisplayCompact({
  pattern,
  interval = 1,
  days = null,
  className,
}: Pick<RecurrenceDisplayProps, 'pattern' | 'interval' | 'days' | 'className'>) {
  return (
    <RecurrenceDisplay
      pattern={pattern}
      interval={interval}
      days={days}
      className={className}
      size="small"
      showIcon={false}
    />
  )
}

/**
 * Full version with all details
 */
export function RecurrenceDisplayFull({
  pattern,
  interval = 1,
  days = null,
  endDate = null,
  nextOccurrence = null,
  className,
}: RecurrenceDisplayProps) {
  return (
    <RecurrenceDisplay
      pattern={pattern}
      interval={interval}
      days={days}
      endDate={endDate}
      nextOccurrence={nextOccurrence}
      className={className}
      size="medium"
      showIcon={true}
      showEndDate={true}
      showNextOccurrence={true}
    />
  )
}
