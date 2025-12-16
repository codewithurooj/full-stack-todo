/**
 * Authentication Utilities
 * Frontend uses backend API for all auth operations
 * See lib/api/auth.ts for authentication functions
 */

/**
 * Get JWT token from localStorage
 */
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('auth_token')
}

/**
 * Set JWT token in localStorage
 */
export function setAuthToken(token: string): void {
  if (typeof window === 'undefined') return
  localStorage.setItem('auth_token', token)
}

/**
 * Remove JWT token from localStorage
 */
export function removeAuthToken(): void {
  if (typeof window === 'undefined') return
  localStorage.removeItem('auth_token')
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return getAuthToken() !== null
}

export type Session = {
  user: {
    id: string
    email: string
    name: string | null
  }
  token: string
}
