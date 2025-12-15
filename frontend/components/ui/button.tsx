/**
 * Button Component
 * Reusable button with variants and loading states
 * Based on specs/ui/shared-ui.md
 */

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-lg text-base font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed",
  {
    variants: {
      variant: {
        primary: "bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800 active:from-blue-800 active:to-blue-900 shadow-md hover:shadow-lg hover:shadow-blue-500/50 hover:-translate-y-0.5",
        secondary: "border-2 border-blue-600 text-blue-600 hover:bg-blue-50 active:bg-blue-100 hover:border-blue-700 shadow-sm hover:shadow-md hover:-translate-y-0.5",
        danger: "bg-gradient-to-r from-red-600 to-red-700 text-white hover:from-red-700 hover:to-red-800 active:from-red-800 active:to-red-900 shadow-md hover:shadow-lg hover:shadow-red-500/50 hover:-translate-y-0.5",
        ghost: "hover:bg-gray-100 active:bg-gray-200 hover:shadow-sm",
        link: "text-blue-600 underline-offset-4 hover:underline hover:text-blue-700",
      },
      size: {
        small: "h-9 px-4 text-sm",
        medium: "h-11 px-6",
        large: "h-13 px-8 text-lg",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "medium",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  loading?: boolean
  fullWidth?: boolean
  icon?: React.ReactNode
  iconPosition?: "left" | "right"
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      loading = false,
      fullWidth = false,
      icon,
      iconPosition = "left",
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        className={cn(
          buttonVariants({ variant, size, className }),
          fullWidth && "w-full"
        )}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <Loader2 className="h-4 w-4 animate-spin" />}
        {!loading && icon && iconPosition === "left" && icon}
        {children}
        {!loading && icon && iconPosition === "right" && icon}
      </button>
    )
  }
)

Button.displayName = "Button"

export { Button, buttonVariants }
