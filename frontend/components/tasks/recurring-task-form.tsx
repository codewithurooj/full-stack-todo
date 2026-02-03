/**
 * RecurringTaskForm Component
 * Form section for setting recurring task patterns
 * Based on specs/010-recurring-due-dates/spec.md - T091
 */

"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { CalendarDays, CalendarRange, Calendar, Settings2 } from "lucide-react"
import { useRecurring, RecurringPattern } from "@/hooks/useRecurring"

export interface RecurringTaskFormProps {
  userId?: string
  taskId?: number
  initialPattern?: string | null
  initialInterval?: number | null
  initialDays?: string[] | null
  initialEndDate?: string | null
  onChange?: (pattern: RecurringPattern, interval: number, days: string[] | null, endDate: string | null) => void
  className?: string
  showAdvanced?: boolean
}

const WEEKDAY_OPTIONS = [
  { value: 'Mon', label: 'Mon' },
  { value: 'Tue', label: 'Tue' },
  { value: 'Wed', label: 'Wed' },
  { value: 'Thu', label: 'Thu' },
  { value: 'Fri', label: 'Fri' },
  { value: 'Sat', label: 'Sat' },
  { value: 'Sun', label: 'Sun' },
]

export function RecurringTaskForm({
  userId,
  taskId,
  initialPattern = null,
  initialInterval = 1,
  initialDays = null,
  initialEndDate = null,
  onChange,
  className,
  showAdvanced = false,
}: RecurringTaskFormProps) {
  const {
    pattern,
    interval,
    days,
    endDate,
    setPattern,
    setInterval,
    setDays,
    setEndDate,
    validationError,
  } = useRecurring(userId, taskId, {
    recurring_pattern: initialPattern,
    recurring_interval: initialInterval,
    recurring_days: initialDays,
    recurring_end_date: initialEndDate,
  } as any)

  // Notify parent of changes
  React.useEffect(() => {
    if (onChange) {
      onChange(pattern, interval, days, endDate)
    }
  }, [pattern, interval, days, endDate, onChange])

  const handlePatternChange = (value: string) => {
    const newPattern = value === 'none' ? null : (value as RecurringPattern)
    setPattern(newPattern)

    // Reset days if switching patterns
    if (newPattern !== 'weekly') {
      setDays(null)
    }
  }

  const handleDayToggle = (day: string) => {
    const currentDays = days || []
    if (currentDays.includes(day)) {
      setDays(currentDays.filter(d => d !== day))
    } else {
      setDays([...currentDays, day])
    }
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Pattern Selection */}
      <div className="space-y-3">
        <Label className="text-sm font-medium">Repeat Pattern</Label>
        <RadioGroup
          value={pattern || 'none'}
          onValueChange={handlePatternChange}
          className="space-y-2"
        >
          {/* No repeat */}
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="none" id="pattern-none" />
            <Label htmlFor="pattern-none" className="flex items-center gap-2 cursor-pointer font-normal">
              <Calendar size={16} className="text-muted-foreground" />
              <span>Does not repeat</span>
            </Label>
          </div>

          {/* Daily */}
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="daily" id="pattern-daily" />
            <Label htmlFor="pattern-daily" className="flex items-center gap-2 cursor-pointer font-normal">
              <CalendarDays size={16} className="text-blue-600" />
              <span>Daily</span>
            </Label>
          </div>

          {/* Weekly */}
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="weekly" id="pattern-weekly" />
            <Label htmlFor="pattern-weekly" className="flex items-center gap-2 cursor-pointer font-normal">
              <CalendarRange size={16} className="text-green-600" />
              <span>Weekly</span>
            </Label>
          </div>

          {/* Monthly */}
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="monthly" id="pattern-monthly" />
            <Label htmlFor="pattern-monthly" className="flex items-center gap-2 cursor-pointer font-normal">
              <Calendar size={16} className="text-purple-600" />
              <span>Monthly</span>
            </Label>
          </div>

          {/* Custom (if showAdvanced) */}
          {showAdvanced && (
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="custom" id="pattern-custom" />
              <Label htmlFor="pattern-custom" className="flex items-center gap-2 cursor-pointer font-normal">
                <Settings2 size={16} className="text-orange-600" />
                <span>Custom</span>
              </Label>
            </div>
          )}
        </RadioGroup>
      </div>

      {/* Weekly: Day Selection */}
      {pattern === 'weekly' && (
        <div className="space-y-3 pt-2 border-t">
          <Label className="text-sm font-medium">Repeat On</Label>
          <div className="flex gap-2 flex-wrap">
            {WEEKDAY_OPTIONS.map(({ value, label }) => (
              <div key={value} className="flex items-center">
                <Checkbox
                  id={`day-${value}`}
                  checked={days?.includes(value) || false}
                  onCheckedChange={() => handleDayToggle(value)}
                  className="mr-2"
                />
                <Label
                  htmlFor={`day-${value}`}
                  className="text-sm font-normal cursor-pointer select-none"
                >
                  {label}
                </Label>
              </div>
            ))}
          </div>
          {days && days.length === 0 && (
            <p className="text-xs text-muted-foreground text-red-600">
              Please select at least one day
            </p>
          )}
        </div>
      )}

      {/* Advanced Options */}
      {showAdvanced && pattern && (
        <div className="space-y-3 pt-2 border-t">
          {/* Interval */}
          <div className="space-y-2">
            <Label htmlFor="interval" className="text-sm font-medium">
              Every
            </Label>
            <div className="flex items-center gap-2">
              <Input
                id="interval"
                type="number"
                min="1"
                max="365"
                value={interval}
                onChange={(e) => setInterval(parseInt(e.target.value) || 1)}
                className="w-20"
              />
              <span className="text-sm text-muted-foreground">
                {pattern === 'daily' && (interval === 1 ? 'day' : 'days')}
                {pattern === 'weekly' && (interval === 1 ? 'week' : 'weeks')}
                {pattern === 'monthly' && (interval === 1 ? 'month' : 'months')}
                {pattern === 'custom' && 'period(s)'}
              </span>
            </div>
          </div>

          {/* End Date */}
          <div className="space-y-2">
            <Label htmlFor="end-date" className="text-sm font-medium">
              End Date (Optional)
            </Label>
            <Input
              id="end-date"
              type="date"
              value={endDate || ''}
              onChange={(e) => setEndDate(e.target.value || null)}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              Leave empty for no end date
            </p>
          </div>
        </div>
      )}

      {/* Validation Error */}
      {validationError && (
        <div className="p-3 rounded-md bg-red-50 border border-red-200">
          <p className="text-sm text-red-800">{validationError}</p>
        </div>
      )}
    </div>
  )
}
