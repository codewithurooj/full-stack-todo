/**
 * Checkbox Component
 * Based on specs/ui/shared-ui.md
 */

"use client"

import * as React from "react"
import { Check } from "lucide-react"
import { cn } from "@/lib/utils"

export interface CheckboxProps {
  checked: boolean
  onCheckedChange?: (checked: boolean) => void
  label?: string
  disabled?: boolean
  name?: string
  id?: string
  className?: string
}

export const Checkbox = React.forwardRef<HTMLButtonElement, CheckboxProps>(
  ({ checked, onCheckedChange, label, disabled, name, id, className }, ref) => {
    const checkboxId = id || React.useId()

    const handleClick = () => {
      if (!disabled && onCheckedChange) {
        onCheckedChange(!checked)
      }
    }

    return (
      <div className="flex items-center gap-2">
        <button
          ref={ref}
          type="button"
          role="checkbox"
          aria-checked={checked}
          aria-labelledby={label ? `${checkboxId}-label` : undefined}
          id={checkboxId}
          name={name}
          disabled={disabled}
          onClick={handleClick}
          className={cn(
            "h-5 w-5 rounded border-2 flex items-center justify-center transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 focus-visible:ring-offset-2",
            checked
              ? "bg-blue-600 border-blue-600"
              : "border-gray-300 bg-white hover:border-gray-400",
            disabled && "opacity-50 cursor-not-allowed",
            !disabled && "cursor-pointer",
            className
          )}
        >
          {checked && <Check className="h-4 w-4 text-white" />}
        </button>
        {label && (
          <label
            id={`${checkboxId}-label`}
            htmlFor={checkboxId}
            className={cn(
              "text-sm font-medium text-gray-700 cursor-pointer",
              disabled && "opacity-50 cursor-not-allowed"
            )}
            onClick={!disabled ? handleClick : undefined}
          >
            {label}
          </label>
        )}
      </div>
    )
  }
)

Checkbox.displayName = "Checkbox"
