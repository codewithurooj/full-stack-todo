/**
 * Recurring Tasks Hook
 * React hook for managing recurring task patterns
 */

"use client"

import { useState, useCallback, useEffect } from 'react'
import { Task } from '@/types/task'
import { recurringApi } from '@/lib/api/recurring'
import { validateRecurringPattern } from '@/lib/rrule-parser'

export type RecurringPattern = 'daily' | 'weekly' | 'monthly' | 'custom' | null

export interface RecurringState {
  pattern: RecurringPattern
  interval: number
  days: string[] | null
  endDate: string | null
}

export function useRecurring(userId: string | undefined, taskId: number | undefined, initialTask?: Task) {
  // State for recurring pattern configuration
  const [pattern, setPattern] = useState<RecurringPattern>(
    initialTask?.recurring_pattern as RecurringPattern || null
  )
  const [interval, setInterval] = useState<number>(
    initialTask?.recurring_interval || 1
  )
  const [days, setDays] = useState<string[] | null>(
    initialTask?.recurring_days || null
  )
  const [endDate, setEndDate] = useState<string | null>(
    initialTask?.recurring_end_date || null
  )
  const [nextOccurrence, setNextOccurrence] = useState<string | null>(
    initialTask?.next_occurrence || null
  )

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Validate current pattern configuration
   */
  const isValid = useCallback((): boolean => {
    if (!pattern) return true // No pattern is valid (non-recurring)
    const validationError = validateRecurringPattern(pattern, interval, days || undefined)
    return validationError === null
  }, [pattern, interval, days])

  /**
   * Get validation error message
   */
  const getValidationError = useCallback((): string | null => {
    if (!pattern) return null
    return validateRecurringPattern(pattern, interval, days || undefined)
  }, [pattern, interval, days])

  /**
   * Set recurring pattern on the task
   */
  const setRecurringPattern = async (): Promise<Task | null> => {
    if (!userId || !taskId) {
      setError('User ID or Task ID is missing')
      return null
    }

    if (!pattern) {
      setError('Pattern is required')
      return null
    }

    // Validate before sending
    const validationError = getValidationError()
    if (validationError) {
      setError(validationError)
      return null
    }

    try {
      setLoading(true)
      setError(null)

      const updatedTask = await recurringApi.setRecurring(
        userId,
        taskId,
        pattern,
        interval,
        days || undefined,
        endDate || undefined
      )

      // Update local state with response
      setPattern(updatedTask.recurring_pattern as RecurringPattern)
      setInterval(updatedTask.recurring_interval || 1)
      setDays(updatedTask.recurring_days || null)
      setEndDate(updatedTask.recurring_end_date || null)
      setNextOccurrence(updatedTask.next_occurrence || null)

      return updatedTask
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to set recurring pattern'
      setError(message)
      console.error('Error setting recurring pattern:', err)
      return null
    } finally {
      setLoading(false)
    }
  }

  /**
   * Remove recurring pattern from the task
   */
  const removeRecurringPattern = async (
    deleteType: 'this_only' | 'this_and_future' | 'all' = 'this_only'
  ): Promise<boolean> => {
    if (!userId || !taskId) {
      setError('User ID or Task ID is missing')
      return false
    }

    try {
      setLoading(true)
      setError(null)

      await recurringApi.removeRecurring(userId, taskId, deleteType)

      // Clear local state
      setPattern(null)
      setInterval(1)
      setDays(null)
      setEndDate(null)
      setNextOccurrence(null)

      return true
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to remove recurring pattern'
      setError(message)
      console.error('Error removing recurring pattern:', err)
      return false
    } finally {
      setLoading(false)
    }
  }

  /**
   * Fetch next occurrence for the task
   */
  const fetchNextOccurrence = async (): Promise<string | null> => {
    if (!userId || !taskId) {
      return null
    }

    try {
      const response = await recurringApi.getNextOccurrence(userId, taskId)
      setNextOccurrence(response.next_occurrence)
      return response.next_occurrence
    } catch (err) {
      console.error('Error fetching next occurrence:', err)
      return null
    }
  }

  /**
   * Reset pattern to initial state
   */
  const resetPattern = useCallback(() => {
    setPattern(initialTask?.recurring_pattern as RecurringPattern || null)
    setInterval(initialTask?.recurring_interval || 1)
    setDays(initialTask?.recurring_days || null)
    setEndDate(initialTask?.recurring_end_date || null)
    setNextOccurrence(initialTask?.next_occurrence || null)
    setError(null)
  }, [initialTask])

  /**
   * Clear all pattern fields
   */
  const clearPattern = useCallback(() => {
    setPattern(null)
    setInterval(1)
    setDays(null)
    setEndDate(null)
    setNextOccurrence(null)
    setError(null)
  }, [])

  /**
   * Check if task has a recurring pattern
   */
  const isRecurring = useCallback((): boolean => {
    return pattern !== null
  }, [pattern])

  /**
   * Get current state as object
   */
  const getState = useCallback((): RecurringState => {
    return { pattern, interval, days, endDate }
  }, [pattern, interval, days, endDate])

  /**
   * Set state from object (useful for form initialization)
   */
  const setState = useCallback((state: Partial<RecurringState>) => {
    if (state.pattern !== undefined) setPattern(state.pattern)
    if (state.interval !== undefined) setInterval(state.interval)
    if (state.days !== undefined) setDays(state.days)
    if (state.endDate !== undefined) setEndDate(state.endDate)
  }, [])

  /**
   * Auto-sync with initialTask when it changes
   */
  useEffect(() => {
    if (initialTask) {
      setPattern(initialTask.recurring_pattern as RecurringPattern || null)
      setInterval(initialTask.recurring_interval || 1)
      setDays(initialTask.recurring_days || null)
      setEndDate(initialTask.recurring_end_date || null)
      setNextOccurrence(initialTask.next_occurrence || null)
    }
  }, [initialTask])

  return {
    // State
    pattern,
    interval,
    days,
    endDate,
    nextOccurrence,
    loading,
    error,

    // Setters
    setPattern,
    setInterval,
    setDays,
    setEndDate,

    // Actions
    setRecurringPattern,
    removeRecurringPattern,
    fetchNextOccurrence,
    resetPattern,
    clearPattern,

    // Utilities
    isValid: isValid(),
    validationError: getValidationError(),
    isRecurring: isRecurring(),
    getState,
    setState,
  }
}
