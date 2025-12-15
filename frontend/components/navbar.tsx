/**
 * Navbar Component
 * Application header with auth state
 * Based on specs/ui/shared-ui.md
 */

"use client"

import * as React from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useBackendSession } from "@/lib/use-backend-session"
import { signOutBackend } from "@/lib/api/auth"
import { Button } from "@/components/ui/button"
import { LogOut, User, Menu, X } from "lucide-react"

export function Navbar() {
  const router = useRouter()
  const { data: session, isPending } = useBackendSession()
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false)

  const handleSignOut = async () => {
    await signOutBackend()
    setMobileMenuOpen(false)
    router.push("/auth/signin")
    router.refresh()
  }

  const closeMobileMenu = () => setMobileMenuOpen(false)

  return (
    <header className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white/80 backdrop-blur-lg shadow-sm">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        {/* Logo */}
        <Link href="/" className="group flex items-center gap-2 transition-all duration-200" onClick={closeMobileMenu}>
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 shadow-md group-hover:shadow-lg group-hover:scale-105 transition-all duration-200">
            <span className="text-lg font-bold text-white">T</span>
          </div>
          <h1 className="text-lg sm:text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
            Todo App
          </h1>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center gap-4">
          {isPending ? (
            <div className="h-9 w-24 animate-pulse rounded-lg bg-gray-200" />
          ) : session?.user ? (
            <>
              <Link
                href="/tasks"
                className="relative text-sm font-semibold text-gray-700 hover:text-blue-600 transition-colors duration-200 after:absolute after:bottom-0 after:left-0 after:h-0.5 after:w-0 after:bg-blue-600 after:transition-all after:duration-200 hover:after:w-full"
              >
                My Tasks
              </Link>
              <div className="flex items-center gap-3">
                <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-100 text-sm text-gray-700 border border-gray-200">
                  <div className="h-6 w-6 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                    <User className="h-3.5 w-3.5 text-white" />
                  </div>
                  <span className="font-medium max-w-[150px] truncate">{session.user.email}</span>
                </div>
                <Button
                  variant="ghost"
                  size="small"
                  onClick={handleSignOut}
                  icon={<LogOut className="h-4 w-4" />}
                  className="hover:text-red-600"
                >
                  <span className="hidden lg:inline">Sign Out</span>
                  <span className="lg:hidden">Exit</span>
                </Button>
              </div>
            </>
          ) : (
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="small"
                onClick={() => router.push("/auth/signin")}
              >
                Sign In
              </Button>
              <Button
                variant="primary"
                size="small"
                onClick={() => router.push("/auth/signup")}
              >
                Sign Up
              </Button>
            </div>
          )}
        </nav>

        {/* Mobile Menu Button */}
        <button
          className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors duration-200"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle mobile menu"
        >
          {mobileMenuOpen ? (
            <X className="h-6 w-6 text-gray-700" />
          ) : (
            <Menu className="h-6 w-6 text-gray-700" />
          )}
        </button>
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white/95 backdrop-blur-lg shadow-lg">
          <nav className="container mx-auto px-4 py-4 space-y-3">
            {isPending ? (
              <div className="h-12 w-full animate-pulse rounded-lg bg-gray-200" />
            ) : session?.user ? (
              <>
                {/* User Info */}
                <div className="flex items-center gap-3 p-3 rounded-lg bg-gradient-to-r from-gray-50 to-blue-50 border border-gray-200">
                  <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                    <User className="h-5 w-5 text-white" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-600 font-medium">Signed in as</p>
                    <p className="text-sm font-semibold text-gray-900 truncate">{session.user.email}</p>
                  </div>
                </div>

                {/* My Tasks Link */}
                <Link
                  href="/tasks"
                  onClick={closeMobileMenu}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-blue-50 transition-colors duration-200 border border-transparent hover:border-blue-200"
                >
                  <div className="h-10 w-10 rounded-lg bg-blue-100 flex items-center justify-center">
                    <span className="text-xl">📋</span>
                  </div>
                  <span className="font-semibold text-gray-900">My Tasks</span>
                </Link>

                {/* Sign Out Button */}
                <button
                  onClick={handleSignOut}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-red-50 transition-colors duration-200 w-full border border-transparent hover:border-red-200"
                >
                  <div className="h-10 w-10 rounded-lg bg-red-100 flex items-center justify-center">
                    <LogOut className="h-5 w-5 text-red-600" />
                  </div>
                  <span className="font-semibold text-red-600">Sign Out</span>
                </button>
              </>
            ) : (
              <div className="space-y-3">
                <Button
                  variant="ghost"
                  size="medium"
                  onClick={() => {
                    closeMobileMenu()
                    router.push("/auth/signin")
                  }}
                  className="w-full justify-start"
                >
                  Sign In
                </Button>
                <Button
                  variant="primary"
                  size="medium"
                  onClick={() => {
                    closeMobileMenu()
                    router.push("/auth/signup")
                  }}
                  className="w-full justify-start"
                >
                  Sign Up
                </Button>
              </div>
            )}
          </nav>
        </div>
      )}
    </header>
  )
}
