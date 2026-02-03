/**
 * PriorityBadge Component
 * Visual indicator for task priority (high/medium/low)
 * Based on specs/009-intermediate-features/spec.md - US1
 */

"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export interface PriorityBadgeProps {
  priority: 'high' | 'medium' | 'low'
  className?: string
  size?: 'small' | 'medium'
}

const PRIORITY_STYLES = {
  high: 'bg-red-100 text-red-800 border-red-300',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  low: 'bg-green-100 text-green-800 border-green-300',
}

const PRIORITY_LABELS = {
  high: 'High',
  medium: 'Medium',
  low: 'Low',
}

const SIZE_STYLES = {
  small: 'px-2 py-0.5 text-xs',
  medium: 'px-2.5 py-1 text-sm',
}

export function PriorityBadge({ priority, className, size = 'medium' }: PriorityBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center font-medium rounded-md border transition-all duration-200",
        PRIORITY_STYLES[priority],
        SIZE_STYLES[size],
        className
      )}
    >
      {PRIORITY_LABELS[priority]}
    </span>
  )
}
