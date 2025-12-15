/**
 * Root Layout
 * Application shell with Better Auth session provider
 */

import type { Metadata } from "next"
import "./globals.css"

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
        {children}
      </body>
    </html>
  )
}
