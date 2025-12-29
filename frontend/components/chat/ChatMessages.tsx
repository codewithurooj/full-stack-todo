'use client'

import { useEffect, useRef } from 'react'
import { Message } from '@/types/chat'
import { format } from 'date-fns'

interface ChatMessagesProps {
  messages: Message[]
  isLoading?: boolean
}

/**
 * ChatMessages Component
 * Displays message history with user/AI visual distinction and auto-scroll
 */
export function ChatMessages({ messages, isLoading = false }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // T015: Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 && !isLoading && (
        <div className="flex items-center justify-center h-full">
          <div className="text-center text-gray-500">
            <p className="text-lg font-medium">No messages yet</p>
            <p className="text-sm mt-1">Start a conversation by typing a message below</p>
          </div>
        </div>
      )}

      {messages.map((message, index) => {
        // T013: User/AI visual distinction
        const isUser = message.role === 'user'
        const isSystem = message.role === 'system'

        // Skip system messages in UI
        if (isSystem) return null

        return (
          <div
            key={index}
            className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] rounded-lg px-4 py-2 ${
                isUser
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-900 border border-gray-200'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-semibold">
                  {isUser ? 'You' : 'AI Assistant'}
                </span>
                {message.created_at && (
                  <span className={`text-xs ${isUser ? 'text-blue-100' : 'text-gray-500'}`}>
                    {format(new Date(message.created_at), 'HH:mm')}
                  </span>
                )}
              </div>
              <div className="whitespace-pre-wrap break-words">
                {message.content}
              </div>
              {message.tool_calls && message.tool_calls.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-300">
                  <p className="text-xs opacity-75">
                    🔧 Used tools: {message.tool_calls.join(', ')}
                  </p>
                </div>
              )}
            </div>
          </div>
        )
      })}

      {/* T014: Loading indicator */}
      {isLoading && (
        <div className="flex justify-start">
          <div className="max-w-[70%] rounded-lg px-4 py-2 bg-gray-100 border border-gray-200">
            <div className="flex items-center gap-2">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span className="text-sm text-gray-600">AI is thinking...</span>
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}
