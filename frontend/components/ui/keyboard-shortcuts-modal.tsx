/**
 * Keyboard Shortcuts Help Modal
 * Shows available keyboard shortcuts
 */

"use client"

import * as React from "react"
import { Modal } from "./modal"
import { Keyboard } from "lucide-react"

interface Shortcut {
  keys: string[]
  description: string
  category: string
}

const shortcuts: Shortcut[] = [
  { keys: ["N"], description: "New task", category: "Tasks" },
  { keys: ["?"], description: "Show keyboard shortcuts", category: "General" },
  { keys: ["C"], description: "Open AI chat", category: "Navigation" },
  { keys: ["T"], description: "Go to tasks", category: "Navigation" },
  { keys: ["/"], description: "Focus search (coming soon)", category: "General" },
  { keys: ["Esc"], description: "Close modals", category: "General" },
]

interface KeyboardShortcutsModalProps {
  isOpen: boolean
  onClose: () => void
}

export function KeyboardShortcutsModal({ isOpen, onClose }: KeyboardShortcutsModalProps) {
  const categories = Array.from(new Set(shortcuts.map((s) => s.category)))

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Keyboard Shortcuts">
      <div className="space-y-6">
        {categories.map((category) => (
          <div key={category}>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">{category}</h3>
            <div className="space-y-2">
              {shortcuts
                .filter((s) => s.category === category)
                .map((shortcut, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-sm text-gray-700">{shortcut.description}</span>
                    <div className="flex gap-1">
                      {shortcut.keys.map((key, j) => (
                        <kbd
                          key={j}
                          className="px-2 py-1 text-xs font-semibold text-gray-800 bg-gray-100 border border-gray-300 rounded shadow-sm"
                        >
                          {key}
                        </kbd>
                      ))}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        ))}

        <div className="pt-4 border-t border-gray-200">
          <div className="flex items-start gap-2 text-xs text-gray-600">
            <Keyboard className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <p>
              Press <kbd className="px-1 py-0.5 bg-gray-100 border border-gray-300 rounded">?</kbd>{" "}
              anytime to see this help
            </p>
          </div>
        </div>
      </div>
    </Modal>
  )
}
