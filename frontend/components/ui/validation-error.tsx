/**
 * ValidationError Component
 * Displays validation errors with detailed information
 */

import * as React from "react"
import { Alert } from "@/components/ui/alert"
import { ApiError } from "@/lib/api/client"
import { AlertCircle } from "lucide-react"

export interface ValidationErrorProps {
  error: Error | ApiError | string | null
  onDismiss?: () => void
  className?: string
}

export function ValidationError({ error, onDismiss, className }: ValidationErrorProps) {
  if (!error) return null

  // Extract error message
  let message: string
  let details: string[] = []

  if (typeof error === 'string') {
    message = error
  } else if (error instanceof ApiError) {
    message = error.message

    // Add status code if available
    if (error.status >= 400) {
      details.push(`Status: ${error.status}`)
    }

    // Add error code if available
    if (error.code) {
      details.push(`Code: ${error.code}`)
    }

    // Add details if available
    if (error.details && typeof error.details === 'object') {
      const detailsArray = Object.entries(error.details)
        .filter(([key]) => key !== 'message' && key !== 'detail')
        .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)

      details.push(...detailsArray)
    }
  } else if (error instanceof Error) {
    message = error.message
  } else {
    message = 'An unexpected error occurred'
  }

  return (
    <Alert
      variant="error"
      message={message}
      dismissible
      onClose={onDismiss}
      className={className}
      showIcon={true}
    >
      {details.length > 0 && (
        <div className="mt-2 text-xs space-y-1">
          {details.map((detail, index) => (
            <div key={index} className="flex items-start gap-1">
              <AlertCircle className="h-3 w-3 mt-0.5 flex-shrink-0" />
              <span>{detail}</span>
            </div>
          ))}
        </div>
      )}
    </Alert>
  )
}
