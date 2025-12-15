/**
 * Custom Session Hook for FastAPI Backend
 * Checks session via API endpoint (cookie sent automatically)
 */

"use client"

import { useEffect, useState } from "react"

export interface BackendUser {
  id: string
  email: string
  name: string | null
}

export interface BackendSession {
  user: BackendUser | null
}

/**
 * Fetch session from backend
 * Cookie is sent automatically via credentials: 'include'
 */
async function fetchSession(): Promise<BackendSession> {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/auth/me`,
      {
        credentials: "include", // Send HttpOnly cookie automatically
      }
    )

    if (!response.ok) {
      return { user: null }
    }

    const userData = await response.json()

    return {
      user: {
        id: userData.id,
        email: userData.email,
        name: userData.name,
      },
    }
  } catch (error) {
    // Session not available
    return { user: null }
  }
}

/**
 * Hook to get current session from backend
 */
export function useBackendSession() {
  const [session, setSession] = useState<BackendSession>({ user: null })
  const [isPending, setIsPending] = useState(true)

  useEffect(() => {
    async function loadSession() {
      setIsPending(true)
      const sessionData = await fetchSession()
      setSession(sessionData)
      setIsPending(false)
    }

    loadSession()

    // Periodically check session (in case cookie expires)
    const interval = setInterval(loadSession, 30000) // Check every 30 seconds

    return () => clearInterval(interval)
  }, [])

  return {
    data: session,
    isPending,
  }
}
