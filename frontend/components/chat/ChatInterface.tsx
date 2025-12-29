'use client'

import { useState } from 'react'
import { ChatInput } from './ChatInput'
import { ChatMessages } from './ChatMessages'
import { useChatState } from '@/lib/hooks/use-chat'
import { Plus, ListChecks, Sparkles } from 'lucide-react'

interface ChatInterfaceProps {
  userId: string
}

/**
 * ChatInterface Component
 * T016: Main chat container that connects all chat components
 * T044: Network error handling with retry
 * T045: Mobile responsive styling
 */
export function ChatInterface({ userId }: ChatInterfaceProps) {
  const { messages, isLoading, error, sendMessage, clearError, startNewConversation } = useChatState(userId)
  const [lastMessage, setLastMessage] = useState<string>('')

  // T044: Store last message for retry functionality
  const handleSend = (message: string) => {
    setLastMessage(message)
    sendMessage(message)
  }

  // T044: Retry last message on network error
  const handleRetry = () => {
    if (lastMessage) {
      clearError()
      sendMessage(lastMessage)
    }
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header - T045: Mobile responsive */}
      <div className="flex-shrink-0 bg-blue-500 text-white px-3 sm:px-6 py-3 sm:py-4 border-b border-blue-600">
        <div className="flex items-center justify-between gap-2">
          <div className="flex-1 min-w-0 flex items-center gap-2">
            {/* AI Status Indicator */}
            <div className={`h-2 w-2 rounded-full flex-shrink-0 ${
              isLoading ? 'bg-yellow-400 animate-pulse' : 'bg-green-400'
            }`} />
            <div>
              <h1 className="text-lg sm:text-xl font-semibold truncate">AI Task Assistant</h1>
              <p className="text-xs sm:text-sm text-blue-100 mt-1 hidden sm:block">
                {isLoading ? 'Thinking...' : 'Ready to help'}
              </p>
            </div>
          </div>
          {/* T027: New Conversation Button */}
          {messages.length > 0 && (
            <button
              onClick={startNewConversation}
              disabled={isLoading}
              className="px-3 sm:px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-xs sm:text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
              title="Start a new conversation"
            >
              <span className="hidden sm:inline">New Chat</span>
              <span className="sm:hidden">New</span>
            </button>
          )}
        </div>
      </div>

      {/* T044: Error Banner with Retry - T045: Mobile responsive */}
      {error && (
        <div className="flex-shrink-0 bg-red-50 border-b border-red-200 px-3 sm:px-6 py-2 sm:py-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div className="flex items-start gap-2">
              <span className="text-red-600 font-medium text-sm flex-shrink-0">Error:</span>
              <span className="text-red-700 text-sm">{error}</span>
            </div>
            <div className="flex gap-2 justify-end">
              {lastMessage && (
                <button
                  onClick={handleRetry}
                  disabled={isLoading}
                  className="text-blue-600 hover:text-blue-800 font-medium text-sm disabled:opacity-50"
                >
                  Retry
                </button>
              )}
              <button
                onClick={clearError}
                className="text-red-600 hover:text-red-800 font-medium text-sm"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <ChatMessages messages={messages} isLoading={isLoading} />

      {/* Quick Actions - Show when no messages */}
      {messages.length === 0 && !isLoading && (
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <p className="text-xs text-gray-600 mb-2">Quick actions:</p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handleSend("Add a task to buy groceries")}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-blue-50 text-sm text-gray-700 hover:text-blue-700 rounded-full border border-gray-200 hover:border-blue-300 transition-all hover:scale-105 shadow-sm"
            >
              <Plus className="h-3.5 w-3.5" />
              Add a task
            </button>
            <button
              onClick={() => handleSend("Show me all my tasks")}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-purple-50 text-sm text-gray-700 hover:text-purple-700 rounded-full border border-gray-200 hover:border-purple-300 transition-all hover:scale-105 shadow-sm"
            >
              <ListChecks className="h-3.5 w-3.5" />
              List my tasks
            </button>
            <button
              onClick={() => handleSend("What should I focus on today?")}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-green-50 text-sm text-gray-700 hover:text-green-700 rounded-full border border-gray-200 hover:border-green-300 transition-all hover:scale-105 shadow-sm"
            >
              <Sparkles className="h-3.5 w-3.5" />
              Get suggestions
            </button>
          </div>
        </div>
      )}

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  )
}
