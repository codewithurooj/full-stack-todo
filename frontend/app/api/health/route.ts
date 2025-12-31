// Health check endpoint for Docker container monitoring
// Returns 200 OK when the application is running
export async function GET() {
  return Response.json(
    {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      service: 'frontend',
    },
    { status: 200 }
  )
}
