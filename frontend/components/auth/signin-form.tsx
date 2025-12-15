/**
 * Sign In Form Component
 * Based on specs/ui/authentication-ui.md
 */

"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { signInWithBackend } from "@/lib/api/auth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert } from "@/components/ui/alert"
import Link from "next/link"

export function SignInForm() {
  const router = useRouter()
  const [email, setEmail] = React.useState("")
  const [password, setPassword] = React.useState("")
  const [error, setError] = React.useState("")
  const [loading, setLoading] = React.useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      await signInWithBackend({
        email,
        password,
      })

      // Redirect to tasks page on success
      router.push("/tasks")
      router.refresh() // Refresh to update session
    } catch (err: any) {
      setError(err.message || "Invalid email or password")
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <Alert
          variant="error"
          message={error}
          dismissible
          onClose={() => setError("")}
        />
      )}

      <Input
        type="email"
        label="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Enter your email"
        required
        autoFocus
        disabled={loading}
      />

      <Input
        type="password"
        label="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Enter your password"
        required
        disabled={loading}
      />

      <Button
        type="submit"
        fullWidth
        loading={loading}
      >
        Sign In
      </Button>

      <div className="text-center space-y-2">
        <Link
          href="/auth/forgot-password"
          className="block text-sm text-blue-600 hover:underline"
        >
          Forgot password?
        </Link>
        <p className="text-sm text-gray-600">
          Don't have an account?{" "}
          <Link
            href="/auth/signup"
            className="text-blue-600 hover:underline font-medium"
          >
            Sign up
          </Link>
        </p>
      </div>
    </form>
  )
}
