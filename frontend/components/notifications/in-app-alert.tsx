/**
 * In-App Alert Component
 * Fallback alert for when browser notifications are disabled
 */

"use client"

import * as React from "react"
import { Bell, Clock, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

export interface InAppAlertProps {
  title: string
  message: string
  timestamp?: string
  taskId?: number
  onDismiss: () => void
  onSnooze?: (minutes: number) => void
  onViewTask?: (taskId: number) => void
  showSnoozeOptions?: boolean
}

export function InAppAlert({
  title,
  message,
  timestamp,
  taskId,
  onDismiss,
  onSnooze,
  onViewTask,
  showSnoozeOptions = false,
}: InAppAlertProps) {
  const [showSnooze, setShowSnooze] = React.useState(false)

  const snoozeOptions = [
    { label: "5 min", value: 5 },
    { label: "10 min", value: 10 },
    { label: "30 min", value: 30 },
    { label: "1 hour", value: 60 },
  ]

  const handleSnooze = (minutes: number) => {
    if (onSnooze) {
      onSnooze(minutes)
    }
    onDismiss()
  }

  const handleViewTask = () => {
    if (taskId && onViewTask) {
      onViewTask(taskId)
    }
    onDismiss()
  }

  return (
    <div
      className={cn(
        "fixed top-4 right-4 z-50 max-w-md w-full bg-white rounded-xl border-2 border-blue-200 shadow-2xl shadow-blue-500/20",
        "animate-in slide-in-from-top-5 duration-300"
      )}
      role="alert"
      aria-live="assertive"
    >
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start gap-3 mb-3">
          <div className="p-2 bg-blue-100 rounded-lg flex-shrink-0">
            <Bell className="h-5 w-5 text-blue-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 text-base mb-1 break-words">
              {title}
            </h3>
            <p className="text-sm text-gray-600 leading-relaxed break-words">
              {message}
            </p>
            {timestamp && (
              <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {new Date(timestamp).toLocaleString()}
              </p>
            )}
          </div>
          <button
            onClick={onDismiss}
            className="flex-shrink-0 p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors duration-200 min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="Dismiss alert"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-2">
          {taskId && onViewTask && (
            <Button
              size="small"
              variant="primary"
              onClick={handleViewTask}
              className="flex-1 min-h-[44px]"
            >
              View Task
            </Button>
          )}

          {showSnoozeOptions && onSnooze && !showSnooze && (
            <Button
              size="small"
              variant="secondary"
              onClick={() => setShowSnooze(true)}
              icon={<Clock className="h-4 w-4" />}
              className="flex-1 min-h-[44px]"
            >
              Snooze
            </Button>
          )}

          {!taskId && !showSnoozeOptions && (
            <Button
              size="small"
              variant="ghost"
              onClick={onDismiss}
              className="flex-1 min-h-[44px]"
            >
              Dismiss
            </Button>
          )}
        </div>

        {/* Snooze Options */}
        {showSnooze && (
          <div className="mt-3 pt-3 border-t border-gray-200">
            <p className="text-xs text-gray-600 mb-2 font-medium">
              Remind me in:
            </p>
            <div className="grid grid-cols-2 gap-2">
              {snoozeOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleSnooze(option.value)}
                  className="px-3 py-2 text-sm font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors duration-200 border border-gray-200 hover:border-gray-300 min-h-[44px]"
                >
                  {option.label}
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowSnooze(false)}
              className="w-full mt-2 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors duration-200 min-h-[44px]"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * Alert Container for managing multiple alerts
 */
export interface AlertContainerProps {
  children: React.ReactNode
  maxAlerts?: number
}

export function AlertContainer({ children, maxAlerts = 3 }: AlertContainerProps) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-3 max-w-md w-full pointer-events-none">
      <div className="pointer-events-auto flex flex-col gap-3">
        {React.Children.toArray(children).slice(0, maxAlerts)}
      </div>
      {React.Children.count(children) > maxAlerts && (
        <div className="pointer-events-auto bg-gray-100 border border-gray-300 rounded-lg p-2 text-center text-sm text-gray-600">
          +{React.Children.count(children) - maxAlerts} more notification
          {React.Children.count(children) - maxAlerts !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  )
}
