/**
 * RecurrenceEditor Component
 * Advanced editor for recurring task patterns with preview
 * Based on specs/010-recurring-due-dates/spec.md - T092
 */

"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { RecurringTaskForm } from "./recurring-task-form"
import { RecurrenceDisplay } from "./recurrence-display"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { Eye, EyeOff, Trash2, Save } from "lucide-react"
import { useRecurring, RecurringPattern } from "@/hooks/useRecurring"
import { Task } from "@/types/task"

export interface RecurrenceEditorProps {
  userId?: string
  task?: Task
  onSave?: (pattern: RecurringPattern, interval: number, days: string[] | null, endDate: string | null) => Promise<void>
  onRemove?: (deleteType: 'this_only' | 'this_and_future' | 'all') => Promise<void>
  className?: string
  showPreview?: boolean
  allowRemove?: boolean
}

export function RecurrenceEditor({
  userId,
  task,
  onSave,
  onRemove,
  className,
  showPreview = true,
  allowRemove = true,
}: RecurrenceEditorProps) {
  const [showAdvancedPreview, setShowAdvancedPreview] = React.useState(false)
  const [saving, setSaving] = React.useState(false)
  const [removing, setRemoving] = React.useState(false)

  const {
    pattern,
    interval,
    days,
    endDate,
    nextOccurrence,
    isValid,
    validationError,
    isRecurring,
  } = useRecurring(userId, task?.id, task)

  const handleSave = async () => {
    if (!isValid || !pattern) {
      return
    }

    setSaving(true)
    try {
      if (onSave) {
        await onSave(pattern, interval, days, endDate)
      }
    } catch (error) {
      console.error('Failed to save recurrence:', error)
    } finally {
      setSaving(false)
    }
  }

  const handleRemove = async (deleteType: 'this_only' | 'this_and_future' | 'all') => {
    setRemoving(true)
    try {
      if (onRemove) {
        await onRemove(deleteType)
      }
    } catch (error) {
      console.error('Failed to remove recurrence:', error)
    } finally {
      setRemoving(false)
    }
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Main Form */}
      <RecurringTaskForm
        userId={userId}
        taskId={task?.id}
        initialPattern={task?.recurring_pattern}
        initialInterval={task?.recurring_interval}
        initialDays={task?.recurring_days}
        initialEndDate={task?.recurring_end_date}
        showAdvanced={true}
      />

      {/* Preview Section */}
      {showPreview && pattern && (
        <Card className="p-4 bg-muted/50">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">Preview</h4>
              <Button
                variant="ghost"
                size="small"
                onClick={() => setShowAdvancedPreview(!showAdvancedPreview)}
                className="h-8 px-2"
              >
                {showAdvancedPreview ? (
                  <>
                    <EyeOff size={14} className="mr-1" />
                    <span className="text-xs">Hide Details</span>
                  </>
                ) : (
                  <>
                    <Eye size={14} className="mr-1" />
                    <span className="text-xs">Show Details</span>
                  </>
                )}
              </Button>
            </div>

            <RecurrenceDisplay
              pattern={pattern}
              interval={interval}
              days={days}
              endDate={endDate}
              nextOccurrence={nextOccurrence}
              showEndDate={showAdvancedPreview}
              showNextOccurrence={showAdvancedPreview}
              size="medium"
            />

            {showAdvancedPreview && (
              <div className="pt-2 space-y-2 text-sm text-muted-foreground">
                <div className="flex justify-between">
                  <span>Interval:</span>
                  <span className="font-medium">Every {interval} {getIntervalUnit(pattern, interval)}</span>
                </div>
                {days && days.length > 0 && (
                  <div className="flex justify-between">
                    <span>Days:</span>
                    <span className="font-medium">{days.join(', ')}</span>
                  </div>
                )}
                {endDate && (
                  <div className="flex justify-between">
                    <span>Ends:</span>
                    <span className="font-medium">{formatDate(endDate)}</span>
                  </div>
                )}
                {nextOccurrence && (
                  <div className="flex justify-between">
                    <span>Next:</span>
                    <span className="font-medium">{formatDate(nextOccurrence)}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2 pt-2">
        {/* Save Button */}
        {onSave && pattern && (
          <Button
            onClick={handleSave}
            disabled={!isValid || saving}
            className="flex-1"
          >
            {saving ? (
              <>Saving...</>
            ) : (
              <>
                <Save size={16} className="mr-2" />
                Save Recurrence
              </>
            )}
          </Button>
        )}

        {/* Remove Button */}
        {allowRemove && isRecurring && onRemove && (
          <RemoveRecurrenceButton
            onRemove={handleRemove}
            removing={removing}
          />
        )}
      </div>

      {/* Validation Error */}
      {!isValid && validationError && (
        <div className="p-3 rounded-md bg-red-50 border border-red-200">
          <p className="text-sm text-red-800">{validationError}</p>
        </div>
      )}
    </div>
  )
}

/**
 * Remove Recurrence Button with Delete Options
 */
function RemoveRecurrenceButton({
  onRemove,
  removing,
}: {
  onRemove: (deleteType: 'this_only' | 'this_and_future' | 'all') => Promise<void>
  removing: boolean
}) {
  const [showOptions, setShowOptions] = React.useState(false)

  return (
    <div className="relative">
      <Button
        variant="danger"
        onClick={() => setShowOptions(!showOptions)}
        disabled={removing}
        className="flex items-center gap-2"
      >
        <Trash2 size={16} />
        {removing ? 'Removing...' : 'Remove'}
      </Button>

      {showOptions && (
        <Card className="absolute right-0 bottom-full mb-2 w-64 p-2 space-y-1 shadow-lg z-10">
          <Button
            variant="ghost"
            size="small"
            onClick={() => {
              onRemove('this_only')
              setShowOptions(false)
            }}
            className="w-full justify-start text-left"
          >
            <div>
              <div className="font-medium">This Task Only</div>
              <div className="text-xs text-muted-foreground">Keep other occurrences</div>
            </div>
          </Button>
          <Separator />
          <Button
            variant="ghost"
            size="small"
            onClick={() => {
              onRemove('this_and_future')
              setShowOptions(false)
            }}
            className="w-full justify-start text-left"
          >
            <div>
              <div className="font-medium">This & Future</div>
              <div className="text-xs text-muted-foreground">Delete upcoming instances</div>
            </div>
          </Button>
          <Separator />
          <Button
            variant="ghost"
            size="small"
            onClick={() => {
              onRemove('all')
              setShowOptions(false)
            }}
            className="w-full justify-start text-left text-red-600 hover:text-red-700"
          >
            <div>
              <div className="font-medium">All Instances</div>
              <div className="text-xs text-muted-foreground">Delete entire series</div>
            </div>
          </Button>
        </Card>
      )}
    </div>
  )
}

/**
 * Helper: Get interval unit text
 */
function getIntervalUnit(pattern: string, interval: number): string {
  const singular = interval === 1
  switch (pattern) {
    case 'daily':
      return singular ? 'day' : 'days'
    case 'weekly':
      return singular ? 'week' : 'weeks'
    case 'monthly':
      return singular ? 'month' : 'months'
    case 'custom':
      return singular ? 'period' : 'periods'
    default:
      return ''
  }
}

/**
 * Helper: Format date for display
 */
function formatDate(isoDate: string): string {
  try {
    const date = new Date(isoDate)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  } catch (error) {
    return isoDate
  }
}
