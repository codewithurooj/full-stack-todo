/**
 * Toast Notification Component
 * Shows success, error, info, and warning messages
 */

"use client"

import * as React from "react"
import { CheckCircle2, XCircle, Info, AlertTriangle, X } from "lucide-react"

export type ToastType = "success" | "error" | "info" | "warning"

export interface Toast {
  id: string
  type: ToastType
  message: string
  duration?: number
}

interface ToastContextType {
  toasts: Toast[]
  showToast: (message: string, type?: ToastType, duration?: number) => void
  removeToast: (id: string) => void
}

const ToastContext = React.createContext<ToastContextType | undefined>(undefined)

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([])
  const recentToastsRef = React.useRef<Set<string>>(new Set())

  const removeToast = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const showToast = React.useCallback((message: string, type: ToastType = "success", duration: number = 3000) => {
    // Prevent duplicate toasts with the same message within 500ms
    const toastKey = `${type}:${message}`
    if (recentToastsRef.current.has(toastKey)) {
      return
    }

    recentToastsRef.current.add(toastKey)
    setTimeout(() => {
      recentToastsRef.current.delete(toastKey)
    }, 500)

    const id = Math.random().toString(36).substring(7)
    const toast: Toast = { id, type, message, duration }

    setToasts((prev) => [...prev, toast])

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id))
      }, duration)
    }
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, showToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = React.useContext(ToastContext)
  if (!context) {
    throw new Error("useToast must be used within ToastProvider")
  }
  return context
}

interface ToastContainerProps {
  toasts: Toast[]
  onRemove: (id: string) => void
}

function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  if (toasts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-[9999] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast, index) => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onRemove={onRemove}
          index={index}
        />
      ))}
    </div>
  )
}

interface ToastItemProps {
  toast: Toast
  onRemove: (id: string) => void
  index: number
}

function ToastItem({ toast, onRemove, index }: ToastItemProps) {
  const [isExiting, setIsExiting] = React.useState(false)

  const handleRemove = () => {
    setIsExiting(true)
    setTimeout(() => onRemove(toast.id), 300)
  }

  const config = {
    success: {
      icon: CheckCircle2,
      bgColor: "bg-green-50",
      borderColor: "border-green-200",
      textColor: "text-green-800",
      iconColor: "text-green-600",
    },
    error: {
      icon: XCircle,
      bgColor: "bg-red-50",
      borderColor: "border-red-200",
      textColor: "text-red-800",
      iconColor: "text-red-600",
    },
    warning: {
      icon: AlertTriangle,
      bgColor: "bg-yellow-50",
      borderColor: "border-yellow-200",
      textColor: "text-yellow-800",
      iconColor: "text-yellow-600",
    },
    info: {
      icon: Info,
      bgColor: "bg-blue-50",
      borderColor: "border-blue-200",
      textColor: "text-blue-800",
      iconColor: "text-blue-600",
    },
  }

  const { icon: Icon, bgColor, borderColor, textColor, iconColor } = config[toast.type]

  return (
    <div
      className={`pointer-events-auto transition-all duration-300 ${
        isExiting
          ? "translate-x-full opacity-0"
          : "translate-x-0 opacity-100"
      }`}
      style={{
        animationName: isExiting ? undefined : "slideInRight",
        animationDuration: "0.3s",
        animationTimingFunction: "ease-out",
        animationDelay: `${index * 50}ms`,
      }}
    >
      <div
        className={`${bgColor} ${borderColor} ${textColor} border-2 rounded-lg shadow-lg p-4 flex items-start gap-3 max-w-sm relative overflow-hidden`}
      >
        <Icon className={`${iconColor} h-5 w-5 flex-shrink-0 mt-0.5`} />
        <p className="text-sm font-medium flex-1">{toast.message}</p>
        <button
          onClick={handleRemove}
          className={`${textColor} hover:opacity-70 transition-opacity`}
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>

        {/* Progress bar */}
        {toast.duration && toast.duration > 0 && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/10">
            <div
              className="h-full bg-black/20"
              style={{
                animation: `shrink ${toast.duration}ms linear`,
                transformOrigin: "left",
              }}
            />
          </div>
        )}
      </div>
    </div>
  )
}

// Add to global CSS
const styles = `
@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes shrink {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}
`

// Inject styles
if (typeof document !== "undefined") {
  const styleSheet = document.createElement("style")
  styleSheet.textContent = styles
  document.head.appendChild(styleSheet)
}
