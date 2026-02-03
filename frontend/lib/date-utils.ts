/**
 * Date Utilities for Due Date Management
 * Handles date formatting, timezone conversion, and relative time calculations
 */

import { format, formatDistanceToNow, parseISO, isPast, isToday, isThisWeek, isThisMonth, addDays, addWeeks, startOfDay, endOfDay } from 'date-fns'
import { formatInTimeZone, toZonedTime, fromZonedTime } from 'date-fns-tz'

/**
 * Format due date as "Feb 15, 9:00 AM"
 */
export function formatDueDate(dateString: string | null | undefined): string {
  if (!dateString) return ''

  try {
    const date = parseISO(dateString)
    return format(date, 'MMM d, h:mm a')
  } catch {
    return dateString
  }
}

/**
 * Format relative due date as "in 2 hours", "2 days ago"
 */
export function formatRelativeDue(dateString: string | null | undefined): string {
  if (!dateString) return ''

  try {
    const date = parseISO(dateString)
    return formatDistanceToNow(date, { addSuffix: true })
  } catch {
    return dateString
  }
}

/**
 * Check if a task is overdue
 * A task is overdue if:
 * - It has a due date
 * - The due date is in the past
 * - The task is not completed
 */
export function isOverdue(dueDate: string | null | undefined, completed: boolean): boolean {
  if (!dueDate || completed) return false

  try {
    const date = parseISO(dueDate)
    return isPast(date)
  } catch {
    return false
  }
}

/**
 * Calculate how overdue a task is in human-readable format
 * Returns "2 days overdue", "3 hours overdue", etc.
 */
export function getOverdueText(dueDate: string | null | undefined): string {
  if (!dueDate) return ''

  try {
    const date = parseISO(dueDate)
    const distance = formatDistanceToNow(date)
    return `${distance} overdue`
  } catch {
    return 'Overdue'
  }
}

/**
 * Parse user input to ISO 8601 date string
 * Supports:
 * - Date objects
 * - ISO 8601 strings
 * - Date + time strings
 */
export function parseDueDateInput(input: string | Date): string {
  if (input instanceof Date) {
    return input.toISOString()
  }

  try {
    const date = parseISO(input)
    return date.toISOString()
  } catch {
    return new Date(input).toISOString()
  }
}

/**
 * Convert UTC date to user's local timezone
 */
export function convertToUserTimezone(utcDate: string): Date {
  try {
    const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone
    return toZonedTime(parseISO(utcDate), userTimezone)
  } catch {
    return parseISO(utcDate)
  }
}

/**
 * Convert local date to UTC with timezone information
 */
export function convertToUTC(localDate: Date, timezone?: string): string {
  try {
    const tz = timezone || Intl.DateTimeFormat().resolvedOptions().timeZone
    return fromZonedTime(localDate, tz).toISOString()
  } catch {
    return localDate.toISOString()
  }
}

/**
 * Get user's current timezone
 */
export function getUserTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone
  } catch {
    return 'UTC'
  }
}

/**
 * Format date in user's timezone
 */
export function formatInUserTimezone(date: string | Date, formatStr: string): string {
  try {
    const userTimezone = getUserTimezone()
    const dateObj = typeof date === 'string' ? parseISO(date) : date
    return formatInTimeZone(dateObj, userTimezone, formatStr)
  } catch {
    return typeof date === 'string' ? date : date.toISOString()
  }
}

/**
 * Quick date options for due date picker
 */
export function getQuickDateOptions(): Array<{ label: string; date: Date }> {
  const now = new Date()

  return [
    {
      label: 'Today (5:00 PM)',
      date: new Date(now.getFullYear(), now.getMonth(), now.getDate(), 17, 0, 0)
    },
    {
      label: 'Tomorrow (9:00 AM)',
      date: new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 9, 0, 0)
    },
    {
      label: 'This Weekend (Sat 10:00 AM)',
      date: (() => {
        const daysUntilSaturday = (6 - now.getDay() + 7) % 7 || 7
        return new Date(now.getFullYear(), now.getMonth(), now.getDate() + daysUntilSaturday, 10, 0, 0)
      })()
    },
    {
      label: 'Next Week (Mon 9:00 AM)',
      date: (() => {
        const daysUntilNextMonday = (8 - now.getDay()) % 7 || 7
        return new Date(now.getFullYear(), now.getMonth(), now.getDate() + daysUntilNextMonday, 9, 0, 0)
      })()
    }
  ]
}

/**
 * Check if due date is today
 */
export function isDueToday(dueDate: string | null | undefined): boolean {
  if (!dueDate) return false

  try {
    return isToday(parseISO(dueDate))
  } catch {
    return false
  }
}

/**
 * Check if due date is this week
 */
export function isDueThisWeek(dueDate: string | null | undefined): boolean {
  if (!dueDate) return false

  try {
    return isThisWeek(parseISO(dueDate))
  } catch {
    return false
  }
}

/**
 * Check if due date is this month
 */
export function isDueThisMonth(dueDate: string | null | undefined): boolean {
  if (!dueDate) return false

  try {
    return isThisMonth(parseISO(dueDate))
  } catch {
    return false
  }
}

/**
 * Get CSS class for due date based on urgency
 */
export function getDueDateColorClass(dueDate: string | null | undefined, completed: boolean): string {
  if (!dueDate || completed) return 'text-gray-500'

  try {
    const date = parseISO(dueDate)
    const now = new Date()

    if (isPast(date)) return 'text-red-600'
    if (isToday(parseISO(dueDate))) return 'text-orange-600'
    if (isDueThisWeek(dueDate)) return 'text-yellow-600'

    return 'text-gray-700'
  } catch {
    return 'text-gray-500'
  }
}
