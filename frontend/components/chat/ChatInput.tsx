'use client'

import { useState, FormEvent, KeyboardEvent, useRef, useEffect } from 'react'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

/**
 * ChatInput Component
 * Handles user message input with validation, Enter key support, and auto-resize
 */
export function ChatInput({ onSend, disabled = false }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea based on content
  useEffect(() => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = '44px' // Reset to min height
      const newHeight = Math.min(textarea.scrollHeight, 120) // Max 120px
      textarea.style.height = `${newHeight}px`
    }
  }, [message])

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()

    // T009: Prevent empty messages
    const trimmed = message.trim()
    if (!trimmed) {
      return
    }

    onSend(trimmed)
    setMessage('')
  }

  // T010: Enter key support (Shift+Enter for new line)
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex-shrink-0 border-t border-gray-200 bg-white p-4">
      <div className="flex gap-2">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message... (Shift+Enter for new line)"
          disabled={disabled}
          rows={1}
          aria-label="Chat message input"
          aria-describedby="chat-help-text"
          className="flex-1 resize-none rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed transition-all duration-200"
          style={{ minHeight: '44px', maxHeight: '120px', overflow: 'hidden' }}
        />
      </div>
      <p id="chat-help-text" className="mt-2 text-xs text-gray-500">
        Press Enter to send, Shift+Enter for new line
      </p>
    </form>
  )
}
