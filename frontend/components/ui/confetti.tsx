/**
 * Confetti Animation Component
 * Shows celebration confetti when tasks are completed
 */

"use client"

import * as React from "react"

interface ConfettiProps {
  trigger: boolean
  onComplete?: () => void
}

export function Confetti({ trigger, onComplete }: ConfettiProps) {
  const [show, setShow] = React.useState(false)

  React.useEffect(() => {
    if (trigger) {
      setShow(true)
      const timer = setTimeout(() => {
        setShow(false)
        onComplete?.()
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [trigger, onComplete])

  if (!show) return null

  return (
    <div className="fixed inset-0 pointer-events-none z-[9998]">
      {Array.from({ length: 50 }, (_, i) => (
        <ConfettiPiece key={i} index={i} />
      ))}
    </div>
  )
}

interface ConfettiPieceProps {
  index: number
}

function ConfettiPiece({ index }: ConfettiPieceProps) {
  const colors = [
    "bg-red-500",
    "bg-blue-500",
    "bg-green-500",
    "bg-yellow-500",
    "bg-purple-500",
    "bg-pink-500",
    "bg-orange-500",
  ]

  const randomColor = colors[Math.floor(Math.random() * colors.length)]
  const randomX = Math.random() * 100
  const randomDelay = Math.random() * 0.5
  const randomDuration = 1.5 + Math.random() * 1
  const randomRotation = Math.random() * 360

  return (
    <div
      className={`absolute w-2 h-2 ${randomColor} rounded-sm`}
      style={{
        left: `${randomX}%`,
        top: "-10px",
        animation: `confettiFall ${randomDuration}s ease-out ${randomDelay}s forwards`,
        transform: `rotate(${randomRotation}deg)`,
      }}
    />
  )
}

// Inject confetti animation styles
if (typeof document !== "undefined") {
  const styleSheet = document.createElement("style")
  styleSheet.textContent = `
    @keyframes confettiFall {
      0% {
        transform: translateY(0) rotate(0deg);
        opacity: 1;
      }
      100% {
        transform: translateY(100vh) rotate(720deg);
        opacity: 0;
      }
    }
  `
  if (!document.getElementById("confetti-styles")) {
    styleSheet.id = "confetti-styles"
    document.head.appendChild(styleSheet)
  }
}
