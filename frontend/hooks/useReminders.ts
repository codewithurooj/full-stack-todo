/**
 * Reminders Hook
 * React hook for managing task reminders
 */

"use client"

import { useState, useEffect, useCallback } from 'react'
import { Reminder } from '@/types/task'
import { reminderApi } from '@/lib/api/reminders'

export function useReminders(userId: string | undefined, taskId: number | undefined) {
  const [reminders, setReminders] = useState<Reminder[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  /**
   * Fetch reminders for the task
   */
  const fetchReminders = useCallback(async () => {
    if (!userId || !taskId) {
      setReminders([])
      return
    }

    try {
      setLoading(true)
      setError(null)
      const data = await reminderApi.listReminders(userId, taskId)
      setReminders(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch reminders'
      setError(message)
      console.error('Error fetching reminders:', err)
    } finally {
      setLoading(false)
    }
  }, [userId, taskId])

  /**
   * Create a new reminder
   */
  const createReminder = async (offsetMinutes: number): Promise<Reminder | null> => {
    if (!userId || !taskId) {
      setError('User ID or Task ID is missing')
      return null
    }

    try {
      setLoading(true)
      setError(null)
      const newReminder = await reminderApi.createReminder(userId, taskId, offsetMinutes)

      // Add to local state
      setReminders((prev) => [...prev, newReminder])

      return newReminder
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create reminder'
      setError(message)
      console.error('Error creating reminder:', err)
      return null
    } finally {
      setLoading(false)
    }
  }

  /**
   * Delete a reminder
   */
  const deleteReminder = async (reminderId: number): Promise<boolean> => {
    if (!userId || !taskId) {
      setError('User ID or Task ID is missing')
      return false
    }

    try {
      setLoading(true)
      setError(null)
      await reminderApi.deleteReminder(userId, taskId, reminderId)

      // Remove from local state
      setReminders((prev) => prev.filter((r) => r.id !== reminderId))

      return true
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete reminder'
      setError(message)
      console.error('Error deleting reminder:', err)
      return false
    } finally {
      setLoading(false)
    }
  }

  /**
   * Snooze a reminder
   */
  const snoozeReminder = async (
    reminderId: number,
    snoozeMinutes: number = 10
  ): Promise<Reminder | null> => {
    if (!userId || !taskId) {
      setError('User ID or Task ID is missing')
      return null
    }

    try {
      setLoading(true)
      setError(null)
      const snoozedReminder = await reminderApi.snoozeReminder(
        userId,
        taskId,
        reminderId,
        snoozeMinutes
      )

      // Update in local state
      setReminders((prev) =>
        prev.map((r) => (r.id === reminderId ? snoozedReminder : r))
      )

      return snoozedReminder
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to snooze reminder'
      setError(message)
      console.error('Error snoozing reminder:', err)
      return null
    } finally {
      setLoading(false)
    }
  }

  /**
   * Get count of active (pending) reminders
   */
  const getActiveCount = useCallback((): number => {
    return reminders.filter(
      (r) => !r.delivered && r.delivery_status === 'pending'
    ).length
  }, [reminders])

  /**
   * Get count of all reminders
   */
  const getTotalCount = useCallback((): number => {
    return reminders.length
  }, [reminders])

  /**
   * Check if task has any reminders
   */
  const hasReminders = useCallback((): boolean => {
    return reminders.length > 0
  }, [reminders])

  /**
   * Auto-fetch reminders when userId or taskId changes
   */
  useEffect(() => {
    if (userId && taskId) {
      fetchReminders()
    }
  }, [userId, taskId, fetchReminders])

  return {
    reminders,
    loading,
    error,
    createReminder,
    deleteReminder,
    snoozeReminder,
    refresh: fetchReminders,
    activeCount: getActiveCount(),
    totalCount: getTotalCount(),
    hasReminders: hasReminders(),
  }
}
