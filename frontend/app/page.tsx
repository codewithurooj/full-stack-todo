/**
 * Home Page
 * Landing page with navigation to auth
 */

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { CheckCircle2, ListTodo, Lock, ArrowRight, LogIn } from "lucide-react"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-400/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-purple-400/10 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <div className="container mx-auto px-4 sm:px-6 py-12 sm:py-16 md:py-20 relative">
        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-block mb-4 sm:mb-6">
            <div className="px-3 sm:px-4 py-1.5 sm:py-2 rounded-full bg-blue-100 text-blue-700 text-xs sm:text-sm font-semibold border border-blue-200 shadow-sm">
              ✨ Your productivity companion
            </div>
          </div>

          <h1 className="text-3xl sm:text-4xl md:text-6xl lg:text-7xl font-extrabold mb-4 sm:mb-6 bg-gradient-to-r from-blue-600 via-blue-700 to-purple-600 bg-clip-text text-transparent leading-tight px-2">
            Welcome to Todo App
          </h1>

          <p className="text-base sm:text-lg md:text-xl lg:text-2xl text-gray-600 mb-8 sm:mb-10 leading-relaxed max-w-2xl mx-auto px-4">
            A full-stack todo application built with Next.js and FastAPI.
            Manage your tasks efficiently with a modern, secure interface.
          </p>

          <div className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-4 mb-12 sm:mb-16 md:mb-20 px-4">
            <Link href="/auth/signup" className="w-full sm:w-auto">
              <button className="group relative w-full sm:w-auto px-6 sm:px-8 py-3 sm:py-4 bg-gradient-to-r from-blue-600 via-blue-700 to-purple-600 text-white text-base sm:text-lg font-bold rounded-xl shadow-2xl shadow-blue-500/50 hover:shadow-blue-500/70 transition-all duration-300 hover:scale-105 hover:-translate-y-1 overflow-hidden min-h-[56px]">
                {/* Animated gradient overlay */}
                <div className="absolute inset-0 bg-gradient-to-r from-purple-600 via-blue-700 to-blue-600 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

                {/* Shine effect */}
                <div className="absolute inset-0 translate-x-[-100%] group-hover:translate-x-[100%] bg-gradient-to-r from-transparent via-white/20 to-transparent transition-transform duration-700" />

                <span className="relative flex items-center justify-center gap-2">
                  Get Started
                  <ArrowRight className="h-4 sm:h-5 w-4 sm:w-5 group-hover:translate-x-1 transition-transform duration-300" />
                </span>
              </button>
            </Link>
            <Link href="/auth/signin" className="w-full sm:w-auto">
              <button className="group relative w-full sm:w-auto px-6 sm:px-8 py-3 sm:py-4 bg-white text-blue-700 text-base sm:text-lg font-bold rounded-xl border-2 border-blue-600 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 hover:-translate-y-1 hover:border-blue-700 hover:bg-blue-50 overflow-hidden min-h-[56px]">
                {/* Subtle gradient on hover */}
                <div className="absolute inset-0 bg-gradient-to-r from-blue-50 to-purple-50 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                <span className="relative flex items-center justify-center gap-2">
                  <LogIn className="h-4 sm:h-5 w-4 sm:w-5 group-hover:-translate-x-1 transition-transform duration-300" />
                  Sign In
                </span>
              </button>
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 sm:gap-8 mt-8 sm:mt-12 px-4">
            <div className="group p-6 sm:p-8 rounded-2xl bg-white border-2 border-gray-200 hover:border-blue-300 shadow-lg hover:shadow-2xl hover:shadow-blue-100/50 transition-all duration-300 hover:-translate-y-2">
              <div className="flex flex-col items-center text-center">
                <div className="h-14 w-14 sm:h-16 sm:w-16 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center mb-4 sm:mb-5 group-hover:scale-110 transition-transform duration-300 shadow-lg">
                  <ListTodo className="h-7 w-7 sm:h-8 sm:w-8 text-white" />
                </div>
                <h3 className="text-lg sm:text-xl font-bold mb-2 sm:mb-3 text-gray-900">Task Management</h3>
                <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                  Create, update, and organize your tasks with ease
                </p>
              </div>
            </div>

            <div className="group p-6 sm:p-8 rounded-2xl bg-white border-2 border-gray-200 hover:border-purple-300 shadow-lg hover:shadow-2xl hover:shadow-purple-100/50 transition-all duration-300 hover:-translate-y-2">
              <div className="flex flex-col items-center text-center">
                <div className="h-14 w-14 sm:h-16 sm:w-16 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center mb-4 sm:mb-5 group-hover:scale-110 transition-transform duration-300 shadow-lg">
                  <Lock className="h-7 w-7 sm:h-8 sm:w-8 text-white" />
                </div>
                <h3 className="text-lg sm:text-xl font-bold mb-2 sm:mb-3 text-gray-900">Secure Auth</h3>
                <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                  JWT-based authentication keeps your data safe
                </p>
              </div>
            </div>

            <div className="group p-6 sm:p-8 rounded-2xl bg-white border-2 border-gray-200 hover:border-green-300 shadow-lg hover:shadow-2xl hover:shadow-green-100/50 transition-all duration-300 hover:-translate-y-2 sm:col-span-2 md:col-span-1">
              <div className="flex flex-col items-center text-center">
                <div className="h-14 w-14 sm:h-16 sm:w-16 rounded-2xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center mb-4 sm:mb-5 group-hover:scale-110 transition-transform duration-300 shadow-lg">
                  <CheckCircle2 className="h-7 w-7 sm:h-8 sm:w-8 text-white" />
                </div>
                <h3 className="text-lg sm:text-xl font-bold mb-2 sm:mb-3 text-gray-900">Track Progress</h3>
                <p className="text-sm sm:text-base text-gray-600 leading-relaxed">
                  Mark tasks complete and track your productivity
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
