/**
 * Alert Component
 * Display important messages (success, error, warning, info)
 * Based on specs/ui/shared-ui.md
 */

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from "lucide-react"
import { cn } from "@/lib/utils"

const alertVariants = cva(
  "relative w-full rounded-lg border p-4",
  {
    variants: {
      variant: {
        success: "bg-green-50 border-green-500 text-green-900",
        error: "bg-red-50 border-red-500 text-red-900",
        warning: "bg-yellow-50 border-yellow-500 text-yellow-900",
        info: "bg-blue-50 border-blue-500 text-blue-900",
      },
    },
    defaultVariants: {
      variant: "info",
    },
  }
)

const iconMap = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

export interface AlertProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof alertVariants> {
  title?: string
  message: string
  onClose?: () => void
  dismissible?: boolean
  showIcon?: boolean
  action?: {
    label: string
    onClick: () => void
  }
}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  (
    {
      className,
      variant = "info",
      title,
      message,
      onClose,
      dismissible = false,
      showIcon = true,
      action,
      ...props
    },
    ref
  ) => {
    const Icon = iconMap[variant || "info"]

    return (
      <div
        ref={ref}
        role={variant === "error" || variant === "warning" ? "alert" : "status"}
        className={cn(alertVariants({ variant }), className)}
        {...props}
      >
        <div className="flex gap-3">
          {showIcon && (
            <Icon
              className="h-5 w-5 flex-shrink-0"
              aria-hidden="true"
            />
          )}
          <div className="flex-1">
            {title && (
              <h5 className="mb-1 font-bold text-base">
                {title}
              </h5>
            )}
            <p className="text-sm">{message}</p>
            {action && (
              <button
                onClick={action.onClick}
                className="mt-2 text-sm font-medium underline hover:no-underline"
              >
                {action.label}
              </button>
            )}
          </div>
          {dismissible && onClose && (
            <button
              onClick={onClose}
              className="flex-shrink-0 text-current hover:opacity-70"
              aria-label="Close alert"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>
    )
  }
)

Alert.displayName = "Alert"

export { Alert, alertVariants }
