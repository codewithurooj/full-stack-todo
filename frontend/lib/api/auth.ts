/**
 * Authentication API Client
 * Calls FastAPI backend auth endpoints
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface AuthResponse {
  token: string
  user: {
    id: string
    email: string
    name: string | null
    created_at: string
    updated_at: string
  }
}

export interface SignUpData {
  email: string
  password: string
  name?: string
}

export interface SignInData {
  email: string
  password: string
}

/**
 * Sign up a new user
 */
export async function signUpWithBackend(data: SignUpData): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/api/auth/signup`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Send/receive cookies
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: 'Signup failed',
    }))
    throw new Error(error.detail || 'Signup failed')
  }

  const authData: AuthResponse = await response.json()

  // Cookie is automatically set by backend via Set-Cookie header (HttpOnly)
  // No need to set it manually - credentials: 'include' handles it

  return authData
}

/**
 * Sign in an existing user
 */
export async function signInWithBackend(data: SignInData): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/api/auth/signin`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Send/receive cookies
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: 'Invalid email or password',
    }))
    throw new Error(error.detail || 'Invalid email or password')
  }

  const authData: AuthResponse = await response.json()

  // Cookie is automatically set by backend via Set-Cookie header (HttpOnly)
  // No need to set it manually - credentials: 'include' handles it

  return authData
}

/**
 * Sign out the current user
 */
export async function signOutBackend(): Promise<void> {
  // Call backend signout endpoint to clear the cookie
  try {
    await fetch(`${API_URL}/api/auth/signout`, {
      method: 'POST',
      credentials: 'include',
    })
  } catch (error) {
    // Ignore errors on signout
    console.error('Signout error:', error)
  }
}
