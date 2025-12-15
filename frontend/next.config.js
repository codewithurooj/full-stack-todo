/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  // Fix workspace root detection warning - set to the full-stack-todo directory
  outputFileTracingRoot: require('path').join(__dirname, '../'),
}

module.exports = nextConfig
