/**
 * Browser Notification Service
 * Handles browser notifications with permission management and offline persistence
 */

import { QueuedNotification } from '@/types/task'

const NOTIFICATION_QUEUE_KEY = 'queued_notifications'

/**
 * NotificationService
 * Main service for managing browser notifications
 */
export class NotificationService {
  /**
   * Check if browser supports notifications
   */
  static isSupported(): boolean {
    return typeof window !== 'undefined' && 'Notification' in window
  }

  /**
   * Get current permission status
   */
  static getPermission(): NotificationPermission {
    if (!this.isSupported()) {
      return 'denied'
    }
    return Notification.permission
  }

  /**
   * Request notification permission
   */
  static async requestPermission(): Promise<NotificationPermission> {
    if (!this.isSupported()) {
      console.warn('Notifications are not supported in this browser')
      return 'denied'
    }

    try {
      const permission = await Notification.requestPermission()
      return permission
    } catch (error) {
      console.error('Error requesting notification permission:', error)
      return 'denied'
    }
  }

  /**
   * Show a notification (requires permission)
   */
  static async showNotification(
    title: string,
    options?: NotificationOptions
  ): Promise<Notification | null> {
    if (!this.canShowNotifications()) {
      console.warn('Cannot show notification - permission denied or not supported')
      return null
    }

    try {
      const notification = new Notification(title, {
        icon: '/icon.png',
        badge: '/badge.png',
        ...options,
      })

      return notification
    } catch (error) {
      console.error('Error showing notification:', error)
      return null
    }
  }

  /**
   * Register service worker (placeholder for future push notifications)
   */
  static async registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) {
      console.warn('Service Workers are not supported in this browser')
      return null
    }

    try {
      const registration = await navigator.serviceWorker.register('/service-worker.js')
      console.log('Service Worker registered successfully:', registration)
      return registration
    } catch (error) {
      console.error('Error registering Service Worker:', error)
      return null
    }
  }

  /**
   * Check if notifications are enabled and permitted
   */
  static canShowNotifications(): boolean {
    return this.isSupported() && this.getPermission() === 'granted'
  }
}

/**
 * NotificationQueue
 * Manages offline notification persistence
 */
export class NotificationQueue {
  /**
   * Queue notification for offline delivery
   */
  static queueNotification(notification: QueuedNotification): void {
    try {
      const queue = this.getQueuedNotifications()
      queue.push(notification)
      localStorage.setItem(NOTIFICATION_QUEUE_KEY, JSON.stringify(queue))
    } catch (error) {
      console.error('Error queuing notification:', error)
    }
  }

  /**
   * Get queued notifications
   */
  static getQueuedNotifications(): QueuedNotification[] {
    try {
      const data = localStorage.getItem(NOTIFICATION_QUEUE_KEY)
      return data ? JSON.parse(data) : []
    } catch (error) {
      console.error('Error retrieving queued notifications:', error)
      return []
    }
  }

  /**
   * Clear queue
   */
  static clearQueue(): void {
    try {
      localStorage.removeItem(NOTIFICATION_QUEUE_KEY)
    } catch (error) {
      console.error('Error clearing notification queue:', error)
    }
  }

  /**
   * Process queue (send all queued notifications)
   */
  static processQueue(): void {
    if (!NotificationService.canShowNotifications()) {
      console.warn('Cannot process queue - notifications not permitted')
      return
    }

    try {
      const queue = this.getQueuedNotifications()

      queue.forEach((notification) => {
        NotificationService.showNotification(notification.title, {
          body: notification.body,
          tag: notification.id,
          data: { taskId: notification.taskId },
        })
      })

      // Clear processed notifications
      this.clearQueue()
    } catch (error) {
      console.error('Error processing notification queue:', error)
    }
  }

  /**
   * Remove specific notification from queue
   */
  static removeFromQueue(notificationId: string): void {
    try {
      const queue = this.getQueuedNotifications()
      const filtered = queue.filter((n) => n.id !== notificationId)
      localStorage.setItem(NOTIFICATION_QUEUE_KEY, JSON.stringify(filtered))
    } catch (error) {
      console.error('Error removing notification from queue:', error)
    }
  }
}

/**
 * Request permission flow with explanation
 */
export async function requestPermissionFlow(): Promise<boolean> {
  // Check if already granted
  if (NotificationService.getPermission() === 'granted') {
    return true
  }

  // Check if supported
  if (!NotificationService.isSupported()) {
    console.warn('Browser notifications are not supported')
    return false
  }

  // Request permission
  const result = await NotificationService.requestPermission()

  // Handle result
  if (result === 'denied') {
    console.warn('Notification permission denied by user')
    return false
  }

  return result === 'granted'
}

/**
 * Save notifications to localStorage
 */
export function persistNotifications(notifications: QueuedNotification[]): void {
  try {
    localStorage.setItem(NOTIFICATION_QUEUE_KEY, JSON.stringify(notifications))
  } catch (error) {
    console.error('Error persisting notifications:', error)
  }
}

/**
 * Load persisted notifications from localStorage
 */
export function loadPersistedNotifications(): QueuedNotification[] {
  try {
    const data = localStorage.getItem(NOTIFICATION_QUEUE_KEY)
    return data ? JSON.parse(data) : []
  } catch (error) {
    console.error('Error loading persisted notifications:', error)
    return []
  }
}
