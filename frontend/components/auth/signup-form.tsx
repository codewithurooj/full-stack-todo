/**
 * Sign Up Form Component
 * Based on specs/ui/authentication-ui.md
 */

"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { signUpWithBackend } from "@/lib/api/auth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Alert } from "@/components/ui/alert"
import Link from "next/link"
import { CheckCircle2, Circle } from "lucide-react"

export function SignUpForm() {
  const router = useRouter()
  const [email, setEmail] = React.useState("")
  const [password, setPassword] = React.useState("")
  const [confirmPassword, setConfirmPassword] = React.useState("")
  const [error, setError] = React.useState("")
  const [loading, setLoading] = React.useState(false)

  // Password validation
  const hasMinLength = password.length >= 8
  const hasUppercase = /[A-Z]/.test(password)
  const hasLowercase = /[a-z]/.test(password)
  const hasNumber = /[0-9]/.test(password)
  const passwordsMatch = password === confirmPassword && password.length > 0

  const isPasswordValid = hasMinLength && hasUppercase && hasLowercase && hasNumber
  const canSubmit = isPasswordValid && passwordsMatch && email.length > 0

  // Password strength
  const getPasswordStrength = () => {
    let strength = 0
    if (hasMinLength) strength++
    if (hasUppercase) strength++
    if (hasLowercase) strength++
    if (hasNumber) strength++

    if (strength <= 1) return { label: "Weak", color: "text-red-600" }
    if (strength <= 3) return { label: "Medium", color: "text-yellow-600" }
    return { label: "Strong", color: "text-green-600" }
  }

  const passwordStrength = password ? getPasswordStrength() : null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return

    setError("")
    setLoading(true)

    try {
      await signUpWithBackend({
        email,
        password,
        name: email.split("@")[0], // Use email prefix as name
      })

      // Redirect to tasks page on success
      router.push("/tasks")
      router.refresh() // Refresh to update session
    } catch (err: any) {
      if (err.message?.includes("already registered")) {
        setError("An account with this email already exists")
      } else {
        setError(err.message || "Failed to create account. Please try again.")
      }
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

      <div>
        <Input
          type="password"
          label="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Create a password"
          required
          disabled={loading}
        />
        {password && (
          <div className="mt-2">
            <p className={`text-sm font-medium ${passwordStrength?.color}`}>
              Password strength: {passwordStrength?.label}
            </p>
          </div>
        )}
      </div>

      {password && (
        <div className="bg-gray-50 p-3 rounded-md space-y-1 text-sm">
          <p className="font-medium text-gray-700 mb-2">Password requirements:</p>
          <RequirementItem met={hasMinLength} text="At least 8 characters" />
          <RequirementItem met={hasUppercase} text="Contains uppercase letter" />
          <RequirementItem met={hasLowercase} text="Contains lowercase letter" />
          <RequirementItem met={hasNumber} text="Contains number" />
        </div>
      )}

      <Input
        type="password"
        label="Confirm Password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        placeholder="Confirm your password"
        required
        disabled={loading}
        error={
          confirmPassword && !passwordsMatch
            ? "Passwords do not match"
            : undefined
        }
      />

      <Button
        type="submit"
        fullWidth
        loading={loading}
        disabled={!canSubmit}
      >
        Create Account
      </Button>

      <p className="text-center text-sm text-gray-600">
        Already have an account?{" "}
        <Link
          href="/auth/signin"
          className="text-blue-600 hover:underline font-medium"
        >
          Sign in
        </Link>
      </p>
    </form>
  )
}

function RequirementItem({ met, text }: { met: boolean; text: string }) {
  return (
    <div className="flex items-center gap-2">
      {met ? (
        <CheckCircle2 className="h-4 w-4 text-green-600" />
      ) : (
        <Circle className="h-4 w-4 text-gray-400" />
      )}
      <span className={met ? "text-green-700" : "text-gray-600"}>
        {text}
      </span>
    </div>
  )
}
