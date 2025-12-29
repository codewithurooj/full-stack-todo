/**
 * Root Layout
 * Application shell with Better Auth session provider and Toast notifications
 */

import type { Metadata } from "next"
import "./globals.css"
import { ToastProvider } from "@/components/ui/toast"

export const metadata: Metadata = {
  title: "Todo App - Full Stack",
  description: "A full-stack todo application with Next.js and FastAPI",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        <ToastProvider>
          {children}
        </ToastProvider>
      </body>
    </html>
  )
}
