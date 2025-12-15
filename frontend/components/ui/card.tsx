/**
 * Card Component
 * Container component for grouping related content
 * Based on specs/ui/shared-ui.md
 */

import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const cardVariants = cva(
  "rounded-lg bg-white transition-all",
  {
    variants: {
      variant: {
        default: "border border-gray-200",
        interactive: "border border-gray-200 cursor-pointer hover:shadow-md hover:scale-[1.02]",
        elevated: "shadow-lg hover:shadow-xl",
      },
      padding: {
        none: "p-0",
        small: "p-3",
        medium: "p-4",
        large: "p-6",
      },
    },
    defaultVariants: {
      variant: "default",
      padding: "medium",
    },
  }
)

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {
  header?: React.ReactNode
  footer?: React.ReactNode
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, padding, header, footer, children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(cardVariants({ variant, padding, className }))}
        {...props}
      >
        {header && (
          <div className="border-b border-gray-200 pb-3 mb-3 font-semibold">
            {header}
          </div>
        )}
        {children}
        {footer && (
          <div className="border-t border-gray-200 pt-3 mt-3 text-sm text-gray-600">
            {footer}
          </div>
        )}
      </div>
    )
  }
)

Card.displayName = "Card"

export { Card, cardVariants }
