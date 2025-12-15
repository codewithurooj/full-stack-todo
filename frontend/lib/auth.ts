/**
 * Better Auth Configuration
 * JWT-based authentication with httpOnly cookies
 */

import { betterAuth } from "better-auth"
import { nextCookies } from "better-auth/next-js"
import { Pool } from "pg"

export const auth = betterAuth({
  secret: process.env.BETTER_AUTH_SECRET!,
  baseURL: process.env.BETTER_AUTH_URL || "http://localhost:3000",

  database: new Pool({
    connectionString: process.env.DATABASE_URL!,
  }),

  emailAndPassword: {
    enabled: true,
    requireEmailVerification: false,
  },

  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24, // 1 day
    cookieCache: {
      enabled: true,
      maxAge: 5 * 60, // 5 minutes
      strategy: "jwt", // Store JWT in cookie (compatible with backend JWT decoding)
    },
  },

  plugins: [nextCookies()],
})

export type Session = typeof auth.$Infer.Session
