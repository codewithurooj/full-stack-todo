/**
 * RRULE Parser Utility
 * Converts recurring patterns to human-readable text
 */

import { CalendarDays, CalendarRange, Calendar, type LucideIcon } from 'lucide-react'

/**
 * Convert recurring pattern to human-readable text
 * @param pattern - The recurrence pattern (daily, weekly, monthly, custom)
 * @param interval - The interval (e.g., 1 for daily, 2 for every 2 days)
 * @param days - Optional array of days for weekly patterns (e.g., ['Mon', 'Wed', 'Fri'])
 * @returns Human-readable string
 */
export function formatRecurringPattern(
  pattern: string,
  interval: number = 1,
  days?: string[] | null
): string {
  if (!pattern || pattern === 'none') {
    return 'No repeat'
  }

  switch (pattern.toLowerCase()) {
    case 'daily':
      if (interval === 1) {
        return 'Daily'
      }
      return `Every ${interval} days`

    case 'weekly':
      if (days && days.length > 0) {
        const formattedDays = days.join(', ')
        if (interval === 1) {
          return `Weekly on ${formattedDays}`
        }
        return `Every ${interval} weeks on ${formattedDays}`
      }
      if (interval === 1) {
        return 'Weekly'
      }
      return `Every ${interval} weeks`

    case 'monthly':
      if (interval === 1) {
        return 'Monthly'
      }
      return `Every ${interval} months`

    case 'custom':
      return 'Custom pattern'

    default:
      return pattern
  }
}

/**
 * Convert pattern to short label for badges
 * @param pattern - The recurrence pattern
 * @param interval - The interval
 * @returns Short label string
 */
export function getRecurringLabel(pattern: string, interval: number = 1): string {
  if (!pattern || pattern === 'none') {
    return 'None'
  }

  switch (pattern.toLowerCase()) {
    case 'daily':
      return interval === 1 ? 'Daily' : `${interval}d`

    case 'weekly':
      return interval === 1 ? 'Weekly' : `${interval}w`

    case 'monthly':
      return interval === 1 ? 'Monthly' : `${interval}m`

    case 'custom':
      return 'Custom'

    default:
      return pattern
  }
}

/**
 * Get icon for recurring pattern
 * @param pattern - The recurrence pattern
 * @returns Lucide icon component
 */
export function getRecurringIcon(pattern: string): LucideIcon {
  if (!pattern || pattern === 'none') {
    return Calendar
  }

  switch (pattern.toLowerCase()) {
    case 'daily':
      return CalendarDays

    case 'weekly':
      return CalendarRange

    case 'monthly':
      return Calendar

    case 'custom':
      return Calendar

    default:
      return Calendar
  }
}

/**
 * Format end date for display
 * @param endDate - ISO 8601 date string
 * @returns Formatted date string
 */
export function formatEndDate(endDate: string | null | undefined): string | null {
  if (!endDate) {
    return null
  }

  try {
    const date = new Date(endDate)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return endDate
  }
}

/**
 * Validate recurring pattern parameters
 * @param pattern - The recurrence pattern
 * @param interval - The interval
 * @param days - Optional array of days for weekly patterns
 * @returns Error message or null if valid
 */
export function validateRecurringPattern(
  pattern: string,
  interval: number,
  days?: string[] | null
): string | null {
  if (!pattern || pattern === 'none') {
    return null
  }

  if (interval < 1) {
    return 'Interval must be at least 1'
  }

  if (interval > 365) {
    return 'Interval cannot exceed 365'
  }

  if (pattern === 'weekly' && days && days.length === 0) {
    return 'Please select at least one day for weekly recurrence'
  }

  return null
}
