# Frontend Development Guidelines

## Stack
- **Framework:** Next.js 16+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Authentication:** Better Auth (JWT)

## Project Structure
```
frontend/
├── app/              # Pages and layouts (App Router)
│   ├── (auth)/      # Auth group routes
│   │   ├── login/   # Login page
│   │   └── signup/  # Signup page
│   ├── tasks/       # Task management pages
│   ├── layout.tsx   # Root layout
│   └── page.tsx     # Home page
├── components/       # Reusable components
│   └── ui/          # Base UI components
├── lib/             # Utilities
│   ├── api.ts       # API client
│   ├── auth.ts      # Auth helpers
│   └── utils.ts     # Utility functions
└── public/          # Static assets
```

## Development Patterns

### Server vs Client Components
```tsx
// Server Component (default)
// app/tasks/page.tsx
export default async function TasksPage() {
  // Can fetch data directly
  const tasks = await getTasks()
  return <TaskList tasks={tasks} />
}

// Client Component (interactive)
// components/TaskItem.tsx
'use client'

import { useState } from 'react'

export function TaskItem() {
  const [isEditing, setIsEditing] = useState(false)
  // Interactive features here
}
```

### API Client Usage
All backend calls through `/lib/api.ts`:

```typescript
import { api } from '@/lib/api'

// In Server Component
const tasks = await api.getTasks()

// In Client Component
const handleCreate = async () => {
  const task = await api.createTask({
    title: 'New task',
    description: 'Description'
  })
}
```

### Authentication
Better Auth with JWT stored in httpOnly cookies:

```typescript
// Check auth status
import { auth } from '@/lib/auth'

const session = await auth.getSession()

// Protect routes
if (!session) {
  redirect('/login')
}

// Get user ID
const userId = session.user.id
```

### Styling with Tailwind
```tsx
// Use Tailwind classes
<div className="flex items-center gap-4 p-4 rounded-lg border">
  <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
    Save
  </button>
</div>

// Responsive design
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Content */}
</div>
```

### Error Handling
```tsx
// Use error boundaries
// app/error.tsx
'use client'

export default function Error({ error, reset }) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={reset}>Try again</button>
    </div>
  )
}

// Loading states
// app/loading.tsx
export default function Loading() {
  return <div>Loading...</div>
}
```

## Common Patterns

### Form Handling
```tsx
'use client'

export function TaskForm() {
  const [formData, setFormData] = useState({ title: '', description: '' })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await api.createTask(formData)
      // Success handling
    } catch (error) {
      // Error handling
    }
  }

  return <form onSubmit={handleSubmit}>{/* Form fields */}</form>
}
```

### Data Fetching
```tsx
// Server Component - Direct fetch
export default async function Page() {
  const data = await fetch('...').then(r => r.json())
  return <Component data={data} />
}

// Client Component - Use SWR or React Query
'use client'
import useSWR from 'swr'

export function Component() {
  const { data, error, isLoading } = useSWR('/api/tasks', fetcher)
  if (isLoading) return <Loading />
  if (error) return <Error />
  return <TaskList tasks={data} />
}
```

## TypeScript Types
```typescript
// Define types in lib/types.ts
export interface Task {
  id: number
  user_id: string
  title: string
  description: string | null
  completed: boolean
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  title: string
  description?: string
}

export interface TaskUpdate {
  title?: string
  description?: string
  completed?: boolean
}
```

## Running & Building

```bash
# Development
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Production build
npm run build

# Start production server
npm run start
```

## Environment Variables
Required in `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
BETTER_AUTH_SECRET=your-secret-32-chars-min
```

## Best Practices
- ✅ Use Server Components by default
- ✅ Add 'use client' only when needed
- ✅ Keep components small and focused
- ✅ Use TypeScript for all files
- ✅ Follow Tailwind CSS conventions
- ✅ Handle loading and error states
- ✅ Implement proper error boundaries
- ✅ Use the API client for all requests
- ✅ Never expose secrets in client code

---

**Build fast, type-safe React apps with Next.js!** ⚛️
