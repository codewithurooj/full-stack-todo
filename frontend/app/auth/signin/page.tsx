/**
 * Sign In Page
 * Route: /auth/signin
 * Based on specs/ui/authentication-ui.md
 */

import { SignInForm } from "@/components/auth/signin-form"
import { Card } from "@/components/ui/card"

export default function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Todo App
          </h1>
          <p className="mt-2 text-gray-600">
            Sign in to your account
          </p>
        </div>

        <Card padding="large">
          <SignInForm />
        </Card>
      </div>
    </div>
  )
}
