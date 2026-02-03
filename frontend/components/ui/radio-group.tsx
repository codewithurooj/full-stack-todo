/**
 * RadioGroup Component
 * Radio button group for selecting one option from multiple choices
 */

"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export interface RadioGroupProps {
  value?: string
  onValueChange?: (value: string) => void
  disabled?: boolean
  children: React.ReactNode
  className?: string
}

export interface RadioGroupItemProps extends React.InputHTMLAttributes<HTMLInputElement> {
  value: string
  id: string
  children?: React.ReactNode
}

const RadioGroupContext = React.createContext<{
  value?: string
  onValueChange?: (value: string) => void
  disabled?: boolean
}>({})

export function RadioGroup({ value, onValueChange, disabled, children, className }: RadioGroupProps) {
  return (
    <RadioGroupContext.Provider value={{ value, onValueChange, disabled }}>
      <div role="radiogroup" className={cn("space-y-2", className)}>
        {children}
      </div>
    </RadioGroupContext.Provider>
  )
}

export function RadioGroupItem({ value, id, disabled: itemDisabled, className, children, ...props }: RadioGroupItemProps) {
  const context = React.useContext(RadioGroupContext)
  const disabled = itemDisabled || context.disabled
  const checked = context.value === value

  const handleChange = () => {
    if (!disabled && context.onValueChange) {
      context.onValueChange(value)
    }
  }

  return (
    <div className={cn("flex items-center space-x-2", className)}>
      <input
        type="radio"
        id={id}
        value={value}
        checked={checked}
        onChange={handleChange}
        disabled={disabled}
        className={cn(
          "h-4 w-4 rounded-full border border-gray-300 text-blue-600",
          "focus:ring-2 focus:ring-blue-600 focus:ring-offset-2",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "cursor-pointer"
        )}
        {...props}
      />
      {children && (
        <label
          htmlFor={id}
          className={cn(
            "text-sm font-medium leading-none cursor-pointer",
            disabled && "cursor-not-allowed opacity-50"
          )}
        >
          {children}
        </label>
      )}
    </div>
  )
}
