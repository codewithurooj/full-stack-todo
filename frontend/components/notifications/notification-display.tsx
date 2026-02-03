/**
 * Notification Display Components
 * Badge and alert components for showing notification counts and messages
 */

"use client"

import * as React from "react"
import { Bell, X } from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * NotificationBadge
 * Shows count of undelivered reminders
 */
export interface NotificationBadgeProps {
  count: number
  size?: "small" | "medium" | "large"
  className?: string
}

export function NotificationBadge({
  count,
  size = "medium",
  className
}: NotificationBadgeProps) {
  if (count === 0) return null

  const sizeClasses = {
    small: "h-4 w-4 text-[10px]",
    medium: "h-5 w-5 text-xs",
    large: "h-6 w-6 text-sm",
  }

  return (
    <span
      className={cn(
        "inline-flex items-center justify-center rounded-full bg-gradient-to-r from-red-500 to-red-600 text-white font-bold shadow-sm",
        sizeClasses[size],
        className
      )}
      aria-label={`${count} active reminder${count !== 1 ? 's' : ''}`}
    >
      {count > 99 ? '99+' : count}
    </span>
  )
}

/**
 * InAppAlert
 * Shows in-app alert when browser notifications are denied
 */
export interface InAppAlertProps {
  message: string
  title?: string
  onDismiss: () => void
  variant?: "info" | "warning" | "error" | "success"
  showIcon?: boolean
}

export function InAppAlert({
  message,
  title,
  onDismiss,
  variant = "warning",
  showIcon = true,
}: InAppAlertProps) {
  const variantClasses = {
    info: "bg-blue-50 border-blue-200 text-blue-800",
    warning: "bg-yellow-50 border-yellow-200 text-yellow-800",
    error: "bg-red-50 border-red-200 text-red-800",
    success: "bg-green-50 border-green-200 text-green-800",
  }

  const iconColor = {
    info: "text-blue-500",
    warning: "text-yellow-500",
    error: "text-red-500",
    success: "text-green-500",
  }

  return (
    <div
      className={cn(
        "flex items-start gap-3 p-4 rounded-lg border-2 shadow-sm animate-in slide-in-from-top duration-300",
        variantClasses[variant]
      )}
      role="alert"
    >
      {showIcon && (
        <Bell className={cn("h-5 w-5 flex-shrink-0 mt-0.5", iconColor[variant])} />
      )}
      <div className="flex-1 min-w-0">
        {title && (
          <h4 className="font-semibold text-sm mb-1">{title}</h4>
        )}
        <p className="text-sm leading-relaxed break-words">{message}</p>
      </div>
      <button
        onClick={onDismiss}
        className={cn(
          "flex-shrink-0 p-1 rounded-lg hover:bg-black/5 transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        )}
        aria-label="Dismiss alert"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}

/**
 * NotificationPermissionBanner
 * Banner prompting user to enable notifications
 */
export interface NotificationPermissionBannerProps {
  onEnable: () => void
  onDismiss: () => void
}

export function NotificationPermissionBanner({
  onEnable,
  onDismiss,
}: NotificationPermissionBannerProps) {
  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg p-4 shadow-sm">
      <div className="flex items-start gap-3">
        <Bell className="h-6 w-6 text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-blue-900 mb-1">
            Enable Reminders
          </h4>
          <p className="text-sm text-blue-800 mb-3">
            Get browser notifications for your task reminders. You can manage this anytime in your browser settings.
          </p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={onEnable}
              className="px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors duration-200 shadow-sm hover:shadow-md min-h-[44px]"
            >
              Enable Notifications
            </button>
            <button
              onClick={onDismiss}
              className="px-4 py-2 text-blue-700 text-sm font-semibold rounded-lg hover:bg-blue-100 transition-colors duration-200 min-h-[44px]"
            >
              Maybe Later
            </button>
          </div>
        </div>
        <button
          onClick={onDismiss}
          className="flex-shrink-0 p-1 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
          aria-label="Dismiss banner"
        >
          <X className="h-5 w-5" />
        </button>
      </div>
    </div>
  )
}
