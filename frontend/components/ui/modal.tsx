/**
 * Modal Component
 * Display content in an overlay dialog
 * Based on specs/ui/shared-ui.md
 */

"use client"

import * as React from "react"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  footer?: React.ReactNode
  size?: "small" | "medium" | "large" | "full"
  closeOnOverlayClick?: boolean
  closeOnEscape?: boolean
  showCloseButton?: boolean
}

export function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = "medium",
  closeOnOverlayClick = true,
  closeOnEscape = true,
  showCloseButton = true,
}: ModalProps) {
  const [isAnimating, setIsAnimating] = React.useState(false)

  React.useEffect(() => {
    if (isOpen) {
      setIsAnimating(true)
      document.body.style.overflow = "hidden"
    } else {
      const timer = setTimeout(() => setIsAnimating(false), 200)
      document.body.style.overflow = "unset"
      return () => clearTimeout(timer)
    }

    return () => {
      document.body.style.overflow = "unset"
    }
  }, [isOpen])

  React.useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (closeOnEscape && e.key === "Escape" && isOpen) {
        onClose()
      }
    }

    document.addEventListener("keydown", handleEscape)
    return () => document.removeEventListener("keydown", handleEscape)
  }, [isOpen, closeOnEscape, onClose])

  if (!isOpen && !isAnimating) {
    return null
  }

  const sizeClasses = {
    small: "w-full sm:max-w-md",
    medium: "w-full sm:max-w-2xl",
    large: "w-full sm:max-w-4xl",
    full: "w-[95vw] h-[95vh]",
  }

  return (
    <div
      className={cn(
        "fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 transition-all duration-300",
        isOpen ? "opacity-100" : "opacity-0 pointer-events-none"
      )}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? "modal-title" : undefined}
    >
      {/* Enhanced Backdrop with blur */}
      <div
        className={cn(
          "absolute inset-0 bg-black/60 backdrop-blur-md transition-all duration-300",
          isOpen ? "opacity-100" : "opacity-0"
        )}
        onClick={closeOnOverlayClick ? onClose : undefined}
      />

      {/* Modal content */}
      <div
        className={cn(
          "relative bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl max-h-[95vh] sm:max-h-[90vh] overflow-hidden transition-all duration-300 border-2 border-gray-200",
          sizeClasses[size],
          isOpen ? "scale-100 translate-y-0" : "scale-95 translate-y-4 sm:-translate-y-4"
        )}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white">
            {title && (
              <h2 id="modal-title" className="text-lg sm:text-2xl font-bold text-gray-900">
                {title}
              </h2>
            )}
            {showCloseButton && (
              <button
                onClick={onClose}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-all duration-200 hover:rotate-90 min-h-[44px] min-w-[44px] flex items-center justify-center"
                aria-label="Close modal"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>
        )}

        {/* Content */}
        <div className="overflow-y-auto max-h-[calc(95vh-140px)] sm:max-h-[calc(90vh-140px)] p-4 sm:p-6 bg-white">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="border-t border-gray-200 p-4 sm:p-6 bg-gray-50">
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}
