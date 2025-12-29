/**
 * Chat Page
 * T019: AI-powered task management chat interface with auth protection
 */

'use client'

import * as React from 'react'
import { useRouter } from 'next/navigation'
import { useBackendSession } from '@/lib/use-backend-session'
import { ChatInterface } from '@/components/chat/ChatInterface'
import { Navbar } from '@/components/navbar'

export default function ChatPage() {
  const router = useRouter()
  const { data: session, isPending } = useBackendSession()

  // Redirect to signin if not authenticated
  React.useEffect(() => {
    if (!isPending && !session?.user) {
      router.push('/auth/signin')
    }
  }, [isPending, session, router])

  // Loading state
  if (isPending) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50/30">
        <Navbar />
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto h-[600px] flex items-center justify-center">
            <div className="text-center">
              <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-gray-600">Loading chat...</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Not authenticated
  if (!session?.user) {
    return null
  }

  const userId = session.user.id

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/20 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 right-20 w-72 h-72 bg-blue-400/5 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 left-20 w-72 h-72 bg-purple-400/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <Navbar />

      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-8 relative">
        <div className="max-w-4xl mx-auto">
          {/* Chat Interface Container */}
          <div className="h-[calc(100vh-12rem)] sm:h-[600px]">
            <ChatInterface userId={userId} />
          </div>

          {/* Help Text */}
          <div className="mt-4 text-center text-sm text-gray-600">
            <p>
              Try asking: &quot;Add a task to buy groceries&quot; or &quot;What tasks do I have?&quot;
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
