/**
 * ReminderManager Component
 * Modal for managing task reminders
 */

"use client"

import * as React from "react"
import { Task, Reminder } from "@/types/task"
import { Modal } from "@/components/ui/modal"
import { Button } from "@/components/ui/button"
import { Bell, BellRing, Clock, Trash2, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { useReminders } from "@/hooks/useReminders"
import { NotificationService, requestPermissionFlow } from "@/lib/notification-service"
import { formatDistanceToNow } from "date-fns"

export interface ReminderManagerProps {
  task: Task
  userId: string
  isOpen: boolean
  onClose: () => void
}

export function ReminderManager({
  task,
  userId,
  isOpen,
  onClose,
}: ReminderManagerProps) {
  const {
    reminders,
    loading,
    error,
    createReminder,
    deleteReminder,
    snoozeReminder,
    refresh,
  } = useReminders(userId, task.id)

  const [selectedOffset, setSelectedOffset] = React.useState<number>(15)
  const [permissionStatus, setPermissionStatus] = React.useState<NotificationPermission>('default')
  const [showPermissionPrompt, setShowPermissionPrompt] = React.useState(false)

  // Check notification permission on mount
  React.useEffect(() => {
    if (NotificationService.isSupported()) {
      setPermissionStatus(NotificationService.getPermission())
    }
  }, [])

  // Preset offset options (in minutes)
  const offsetOptions = [
    { label: "5 minutes before", value: 5 },
    { label: "15 minutes before", value: 15 },
    { label: "30 minutes before", value: 30 },
    { label: "1 hour before", value: 60 },
    { label: "1 day before", value: 1440 },
  ]

  const handleCreateReminder = async () => {
    // Check notification permission first
    if (permissionStatus !== 'granted') {
      setShowPermissionPrompt(true)
      return
    }

    const result = await createReminder(selectedOffset)
    if (result) {
      // Successfully created
      console.log('Reminder created:', result)
    }
  }

  const handleRequestPermission = async () => {
    const granted = await requestPermissionFlow()
    setPermissionStatus(granted ? 'granted' : 'denied')
    setShowPermissionPrompt(false)

    if (granted) {
      // Now create the reminder
      await createReminder(selectedOffset)
    }
  }

  const handleDelete = async (reminderId: number) => {
    await deleteReminder(reminderId)
  }

  const handleSnooze = async (reminderId: number, minutes: number) => {
    await snoozeReminder(reminderId, minutes)
  }

  const getRelativeTime = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true })
    } catch {
      return dateString
    }
  }

  const getStatusBadge = (status: Reminder['delivery_status'], delivered: boolean) => {
    if (delivered) {
      return (
        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
          Delivered
        </span>
      )
    }

    const statusColors = {
      pending: "bg-blue-100 text-blue-800",
      sent: "bg-green-100 text-green-800",
      failed: "bg-red-100 text-red-800",
      dismissed: "bg-gray-100 text-gray-800",
      snoozed: "bg-yellow-100 text-yellow-800",
    }

    return (
      <span className={cn(
        "px-2 py-1 text-xs font-semibold rounded-full",
        statusColors[status] || "bg-gray-100 text-gray-800"
      )}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Manage Reminders"
      size="medium"
    >
      <div className="space-y-6">
        {/* Task Info */}
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-semibold text-gray-900 mb-1">{task.title}</h3>
          {task.due_date && (
            <p className="text-sm text-gray-600 flex items-center gap-1">
              <Clock className="h-4 w-4" />
              Due: {new Date(task.due_date).toLocaleString()}
            </p>
          )}
        </div>

        {/* Permission Prompt */}
        {showPermissionPrompt && (
          <div className="p-4 bg-yellow-50 border-2 border-yellow-300 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h4 className="font-semibold text-yellow-900 mb-2">
                  Enable Notifications
                </h4>
                <p className="text-sm text-yellow-800 mb-3">
                  To receive reminders, please enable browser notifications. You can manage this in your browser settings.
                </p>
                <div className="flex gap-2">
                  <Button
                    size="small"
                    variant="primary"
                    onClick={handleRequestPermission}
                  >
                    Enable Notifications
                  </Button>
                  <Button
                    size="small"
                    variant="ghost"
                    onClick={() => setShowPermissionPrompt(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Permission Denied Warning */}
        {permissionStatus === 'denied' && !showPermissionPrompt && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-red-800">
                  Browser notifications are blocked. Please enable them in your browser settings to receive reminders.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Create Reminder Form */}
        <div className="space-y-3">
          <h4 className="font-semibold text-gray-900">Add New Reminder</h4>
          <div className="flex flex-col sm:flex-row gap-3">
            <select
              value={selectedOffset}
              onChange={(e) => setSelectedOffset(Number(e.target.value))}
              className="flex-1 h-10 rounded-lg border border-gray-300 bg-white px-3 py-2 text-base focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
              disabled={!task.due_date}
            >
              {offsetOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <Button
              onClick={handleCreateReminder}
              loading={loading}
              disabled={!task.due_date || loading}
              icon={<Bell className="h-4 w-4" />}
            >
              Add Reminder
            </Button>
          </div>
          {!task.due_date && (
            <p className="text-sm text-gray-600">
              Add a due date to this task before creating reminders.
            </p>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
            {error}
          </div>
        )}

        {/* Existing Reminders */}
        <div className="space-y-3">
          <h4 className="font-semibold text-gray-900">
            Existing Reminders ({reminders.length})
          </h4>

          {reminders.length === 0 ? (
            <div className="p-6 text-center text-gray-500 border-2 border-dashed border-gray-300 rounded-lg">
              <BellRing className="h-12 w-12 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">No reminders set for this task</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {reminders.map((reminder) => (
                <div
                  key={reminder.id}
                  className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <Clock className="h-4 w-4 text-gray-500" />
                        <span className="font-medium text-gray-900">
                          {reminder.offset_minutes < 60
                            ? `${reminder.offset_minutes} minutes before`
                            : reminder.offset_minutes < 1440
                            ? `${Math.floor(reminder.offset_minutes / 60)} hour${Math.floor(reminder.offset_minutes / 60) !== 1 ? 's' : ''} before`
                            : `${Math.floor(reminder.offset_minutes / 1440)} day${Math.floor(reminder.offset_minutes / 1440) !== 1 ? 's' : ''} before`}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">
                        Remind at: {new Date(reminder.remind_at).toLocaleString()}
                      </p>
                      <div className="flex items-center gap-2">
                        {getStatusBadge(reminder.delivery_status, reminder.delivered)}
                        <span className="text-xs text-gray-500">
                          Created {getRelativeTime(reminder.created_at)}
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-col gap-2">
                      {!reminder.delivered && reminder.delivery_status === 'pending' && (
                        <>
                          <Button
                            size="small"
                            variant="ghost"
                            onClick={() => handleSnooze(reminder.id, 10)}
                            icon={<Clock className="h-4 w-4" />}
                            disabled={loading}
                            className="text-xs"
                          >
                            Snooze
                          </Button>
                        </>
                      )}
                      <Button
                        size="small"
                        variant="ghost"
                        onClick={() => handleDelete(reminder.id)}
                        icon={<Trash2 className="h-4 w-4" />}
                        disabled={loading}
                        className="text-red-600 hover:bg-red-50"
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Modal>
  )
}
