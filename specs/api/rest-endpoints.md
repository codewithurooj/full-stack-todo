# REST API Specification: Todo Application

## Overview

This document defines the complete REST API contract for the Full-Stack Todo Application. All endpoints follow RESTful principles and require JWT authentication via Better Auth.

**Base URL:** `https://api.example.com` (replace with actual deployment URL)
**API Version:** v1
**Last Updated:** 2025-12-12

---

## Authentication

**Required:** Yes (all endpoints)
**Type:** Bearer JWT Token
**Header:** `Authorization: Bearer <token>`

### Authentication Flow
1. User signs up/signs in via Better Auth
2. Client receives JWT token
3. Client includes token in `Authorization` header for all API requests
4. Server validates token and extracts `user_id`
5. All operations are scoped to the authenticated user

### Error Responses
- **401 Unauthorized:** Missing or invalid token
- **403 Forbidden:** Valid token but insufficient permissions

---

## Common Response Format

### Success Response Structure
```json
{
  "data": { /* resource or array of resources */ },
  "meta": {
    "timestamp": "2025-12-12T10:00:00Z"
  }
}
```

### Error Response Structure
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { /* additional context */ }
  },
  "meta": {
    "timestamp": "2025-12-12T10:00:00Z"
  }
}
```

---

## Endpoints

### 1. List All Tasks

**Endpoint:** `GET /api/{user_id}/tasks`

**Description:** Retrieves all tasks for the authenticated user. Supports filtering, sorting, and pagination.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | string | Yes | User ID (must match authenticated user) |

#### Query Parameters
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| completed | boolean | No | - | Filter by completion status (true/false) |
| sort | string | No | created_at | Sort field (created_at, updated_at, title) |
| order | string | No | desc | Sort order (asc/desc) |
| limit | integer | No | 50 | Maximum results to return (1-100) |
| offset | integer | No | 0 | Number of results to skip |

#### Request Example
```bash
curl -X GET "https://api.example.com/api/user123/tasks?completed=false&sort=created_at&order=desc" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Success Response (200 OK)
```json
{
  "data": [
    {
      "id": "task_001",
      "user_id": "user123",
      "title": "Complete project documentation",
      "description": "Write comprehensive API documentation for the todo app",
      "completed": false,
      "created_at": "2025-12-10T14:30:00Z",
      "updated_at": "2025-12-10T14:30:00Z"
    },
    {
      "id": "task_002",
      "user_id": "user123",
      "title": "Review pull requests",
      "description": null,
      "completed": true,
      "created_at": "2025-12-09T09:15:00Z",
      "updated_at": "2025-12-11T16:45:00Z"
    }
  ],
  "meta": {
    "timestamp": "2025-12-12T10:00:00Z",
    "total": 2,
    "limit": 50,
    "offset": 0
  }
}
```

#### Error Responses

**401 Unauthorized**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  },
  "meta": {
    "timestamp": "2025-12-12T10:00:00Z"
  }
}
```

**403 Forbidden**
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "User ID in path does not match authenticated user"
  },
  "meta": {
    "timestamp": "2025-12-12T10:00:00Z"
  }
}
```

**400 Bad Request**
```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid query parameter",
    "details": {
      "parameter": "limit",
      "error": "Value must be between 1 and 100"
    }
  },
  "meta": {
    "timestamp": "2025-12-12T10:00:00Z"
  }
}
```

---

### 2. Create Task

**Endpoint:** `POST /api/{user_id}/tasks`

**Description:** Creates a new task for the authenticated user.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | string | Yes | User ID (must match authenticated user) |

#### Request Body
```json
{
  "title": "Task title",
  "description": "Optional task description"
}
```

#### Validation Rules
- `title`: Required, string, min length 1, max length 200
- `description`: Optional, string, max length 1000

#### Request Example
```bash
curl -X POST "https://api.example.com/api/user123/tasks" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deploy to production",
    "description": "Deploy the todo app to Vercel and Render"
  }'
```

#### Success Response (201 Created)
```json
{
  "data": {
    "id": "task_003",
    "user_id": "user123",
    "title": "Deploy to production",
    "description": "Deploy the todo app to Vercel and Render",
    "completed": false,
    "created_at": "2025-12-12T10:05:00Z",
    "updated_at": "2025-12-12T10:05:00Z"
  },
  "meta": {
    "timestamp": "2025-12-12T10:05:00Z"
  }
}
```

#### Error Responses

**400 Bad Request (Validation Error)**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "title": ["Title is required", "Title must be at least 1 character"],
      "description": ["Description must not exceed 1000 characters"]
    }
  },
  "meta": {
    "timestamp": "2025-12-12T10:05:00Z"
  }
}
```

**401 Unauthorized**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  },
  "meta": {
    "timestamp": "2025-12-12T10:05:00Z"
  }
}
```

**403 Forbidden**
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "User ID in path does not match authenticated user"
  },
  "meta": {
    "timestamp": "2025-12-12T10:05:00Z"
  }
}
```

---

### 3. Get Task Details

**Endpoint:** `GET /api/{user_id}/tasks/{id}`

**Description:** Retrieves a specific task by ID. Only returns tasks owned by the authenticated user.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | string | Yes | User ID (must match authenticated user) |
| id | string | Yes | Task ID |

#### Request Example
```bash
curl -X GET "https://api.example.com/api/user123/tasks/task_001" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Success Response (200 OK)
```json
{
  "data": {
    "id": "task_001",
    "user_id": "user123",
    "title": "Complete project documentation",
    "description": "Write comprehensive API documentation for the todo app",
    "completed": false,
    "created_at": "2025-12-10T14:30:00Z",
    "updated_at": "2025-12-10T14:30:00Z"
  },
  "meta": {
    "timestamp": "2025-12-12T10:10:00Z"
  }
}
```

#### Error Responses

**404 Not Found**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Task not found or does not belong to authenticated user"
  },
  "meta": {
    "timestamp": "2025-12-12T10:10:00Z"
  }
}
```

**401 Unauthorized**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  },
  "meta": {
    "timestamp": "2025-12-12T10:10:00Z"
  }
}
```

**403 Forbidden**
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "User ID in path does not match authenticated user"
  },
  "meta": {
    "timestamp": "2025-12-12T10:10:00Z"
  }
}
```

---

### 4. Update Task

**Endpoint:** `PUT /api/{user_id}/tasks/{id}`

**Description:** Updates an existing task. Only the provided fields are updated (partial update supported).

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | string | Yes | User ID (must match authenticated user) |
| id | string | Yes | Task ID |

#### Request Body
```json
{
  "title": "Updated task title",
  "description": "Updated task description",
  "completed": true
}
```

All fields are optional. Only provided fields will be updated.

#### Validation Rules
- `title`: Optional, string, min length 1, max length 200
- `description`: Optional, string, max length 1000, nullable
- `completed`: Optional, boolean

#### Request Example
```bash
curl -X PUT "https://api.example.com/api/user123/tasks/task_001" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete project documentation (URGENT)",
    "completed": false
  }'
```

#### Success Response (200 OK)
```json
{
  "data": {
    "id": "task_001",
    "user_id": "user123",
    "title": "Complete project documentation (URGENT)",
    "description": "Write comprehensive API documentation for the todo app",
    "completed": false,
    "created_at": "2025-12-10T14:30:00Z",
    "updated_at": "2025-12-12T10:15:00Z"
  },
  "meta": {
    "timestamp": "2025-12-12T10:15:00Z"
  }
}
```

#### Error Responses

**404 Not Found**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Task not found or does not belong to authenticated user"
  },
  "meta": {
    "timestamp": "2025-12-12T10:15:00Z"
  }
}
```

**400 Bad Request (Validation Error)**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "title": ["Title must be at least 1 character"],
      "completed": ["Must be a boolean value"]
    }
  },
  "meta": {
    "timestamp": "2025-12-12T10:15:00Z"
  }
}
```

**401 Unauthorized**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  },
  "meta": {
    "timestamp": "2025-12-12T10:15:00Z"
  }
}
```

**403 Forbidden**
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "User ID in path does not match authenticated user"
  },
  "meta": {
    "timestamp": "2025-12-12T10:15:00Z"
  }
}
```

---

### 5. Delete Task

**Endpoint:** `DELETE /api/{user_id}/tasks/{id}`

**Description:** Permanently deletes a task. This action cannot be undone.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | string | Yes | User ID (must match authenticated user) |
| id | string | Yes | Task ID |

#### Request Example
```bash
curl -X DELETE "https://api.example.com/api/user123/tasks/task_002" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Success Response (204 No Content)
No response body. Status code 204 indicates successful deletion.

#### Error Responses

**404 Not Found**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Task not found or does not belong to authenticated user"
  },
  "meta": {
    "timestamp": "2025-12-12T10:20:00Z"
  }
}
```

**401 Unauthorized**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  },
  "meta": {
    "timestamp": "2025-12-12T10:20:00Z"
  }
}
```

**403 Forbidden**
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "User ID in path does not match authenticated user"
  },
  "meta": {
    "timestamp": "2025-12-12T10:20:00Z"
  }
}
```

---

### 6. Toggle Task Completion

**Endpoint:** `PATCH /api/{user_id}/tasks/{id}/complete`

**Description:** Toggles the completion status of a task. If completed=false, sets to true. If completed=true, sets to false.

#### Path Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | string | Yes | User ID (must match authenticated user) |
| id | string | Yes | Task ID |

#### Request Body
No request body required. The endpoint toggles the current state.

#### Request Example
```bash
curl -X PATCH "https://api.example.com/api/user123/tasks/task_001/complete" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Success Response (200 OK)
```json
{
  "data": {
    "id": "task_001",
    "user_id": "user123",
    "title": "Complete project documentation",
    "description": "Write comprehensive API documentation for the todo app",
    "completed": true,
    "created_at": "2025-12-10T14:30:00Z",
    "updated_at": "2025-12-12T10:25:00Z"
  },
  "meta": {
    "timestamp": "2025-12-12T10:25:00Z"
  }
}
```

#### Error Responses

**404 Not Found**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Task not found or does not belong to authenticated user"
  },
  "meta": {
    "timestamp": "2025-12-12T10:25:00Z"
  }
}
```

**401 Unauthorized**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required"
  },
  "meta": {
    "timestamp": "2025-12-12T10:25:00Z"
  }
}
```

**403 Forbidden**
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "User ID in path does not match authenticated user"
  },
  "meta": {
    "timestamp": "2025-12-12T10:25:00Z"
  }
}
```

---

## Data Models

### Task Object
```typescript
interface Task {
  id: string;              // Unique task identifier (UUID)
  user_id: string;         // User who owns this task (UUID)
  title: string;           // Task title (1-200 characters)
  description: string | null; // Optional description (max 1000 characters)
  completed: boolean;      // Completion status (default: false)
  created_at: string;      // ISO 8601 timestamp
  updated_at: string;      // ISO 8601 timestamp
}
```

### Database Constraints
- `id`: Primary key, UUID, auto-generated
- `user_id`: Foreign key to users table, NOT NULL
- `title`: NOT NULL, VARCHAR(200)
- `description`: NULLABLE, VARCHAR(1000)
- `completed`: NOT NULL, BOOLEAN, default false
- `created_at`: NOT NULL, TIMESTAMP, auto-set on creation
- `updated_at`: NOT NULL, TIMESTAMP, auto-updated on modification

### Indexes
- Primary index on `id`
- Index on `user_id` (for fast user-specific queries)
- Composite index on `(user_id, completed)` (for filtered queries)
- Index on `created_at` (for sorting)

---

## Rate Limiting

**Default Limits:**
- 100 requests per minute per user
- 1000 requests per hour per user

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1702378800
```

**Rate Limit Exceeded Response (429 Too Many Requests)**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "details": {
      "retry_after": 60
    }
  },
  "meta": {
    "timestamp": "2025-12-12T10:30:00Z"
  }
}
```

---

## CORS Configuration

**Allowed Origins:**
- Production: `https://your-app.vercel.app`
- Development: `http://localhost:3000`

**Allowed Methods:**
```
GET, POST, PUT, PATCH, DELETE, OPTIONS
```

**Allowed Headers:**
```
Authorization, Content-Type, X-Requested-With
```

**Exposed Headers:**
```
X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
```

**Credentials:** Allowed

---

## Code Examples

### JavaScript/TypeScript (Frontend)

```typescript
// API Client Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const token = localStorage.getItem('auth_token');

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error.message);
  }

  if (response.status === 204) {
    return null; // No content
  }

  return response.json();
}

// List all tasks
async function listTasks(userId: string, filters?: {
  completed?: boolean;
  sort?: string;
  order?: 'asc' | 'desc';
}) {
  const params = new URLSearchParams();
  if (filters?.completed !== undefined) params.set('completed', String(filters.completed));
  if (filters?.sort) params.set('sort', filters.sort);
  if (filters?.order) params.set('order', filters.order);

  const query = params.toString() ? `?${params}` : '';
  return apiRequest(`/api/${userId}/tasks${query}`);
}

// Create a task
async function createTask(userId: string, data: { title: string; description?: string }) {
  return apiRequest(`/api/${userId}/tasks`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// Get task details
async function getTask(userId: string, taskId: string) {
  return apiRequest(`/api/${userId}/tasks/${taskId}`);
}

// Update a task
async function updateTask(userId: string, taskId: string, data: Partial<{
  title: string;
  description: string | null;
  completed: boolean;
}>) {
  return apiRequest(`/api/${userId}/tasks/${taskId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

// Delete a task
async function deleteTask(userId: string, taskId: string) {
  return apiRequest(`/api/${userId}/tasks/${taskId}`, {
    method: 'DELETE',
  });
}

// Toggle task completion
async function toggleTaskComplete(userId: string, taskId: string) {
  return apiRequest(`/api/${userId}/tasks/${taskId}/complete`, {
    method: 'PATCH',
  });
}
```

### Python (Backend Testing)

```python
import requests
from typing import Optional, Dict, Any

class TodoAPIClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def list_tasks(
        self,
        user_id: str,
        completed: Optional[bool] = None,
        sort: str = 'created_at',
        order: str = 'desc'
    ) -> Dict[str, Any]:
        params = {'sort': sort, 'order': order}
        if completed is not None:
            params['completed'] = str(completed).lower()

        response = requests.get(
            f'{self.base_url}/api/{user_id}/tasks',
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()

    def create_task(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        data = {'title': title}
        if description is not None:
            data['description'] = description

        response = requests.post(
            f'{self.base_url}/api/{user_id}/tasks',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

    def get_task(self, user_id: str, task_id: str) -> Dict[str, Any]:
        response = requests.get(
            f'{self.base_url}/api/{user_id}/tasks/{task_id}',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def update_task(
        self,
        user_id: str,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        completed: Optional[bool] = None
    ) -> Dict[str, Any]:
        data = {}
        if title is not None:
            data['title'] = title
        if description is not None:
            data['description'] = description
        if completed is not None:
            data['completed'] = completed

        response = requests.put(
            f'{self.base_url}/api/{user_id}/tasks/{task_id}',
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()

    def delete_task(self, user_id: str, task_id: str) -> None:
        response = requests.delete(
            f'{self.base_url}/api/{user_id}/tasks/{task_id}',
            headers=self.headers
        )
        response.raise_for_status()

    def toggle_task_complete(self, user_id: str, task_id: str) -> Dict[str, Any]:
        response = requests.patch(
            f'{self.base_url}/api/{user_id}/tasks/{task_id}/complete',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage example
client = TodoAPIClient(
    base_url='https://api.example.com',
    token='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
)

# Create a task
task = client.create_task(
    user_id='user123',
    title='Deploy to production',
    description='Deploy the todo app'
)
print(f"Created task: {task['data']['id']}")

# List all incomplete tasks
tasks = client.list_tasks(user_id='user123', completed=False)
print(f"Found {tasks['meta']['total']} incomplete tasks")

# Toggle completion
updated = client.toggle_task_complete(user_id='user123', task_id=task['data']['id'])
print(f"Task completed: {updated['data']['completed']}")

# Delete the task
client.delete_task(user_id='user123', task_id=task['data']['id'])
print("Task deleted")
```

---

## Testing

### Integration Test Scenarios

#### Happy Path
1. **User authenticates** → Receives valid JWT token
2. **Creates task** → Returns 201 with task object
3. **Lists tasks** → Returns 200 with array containing created task
4. **Updates task** → Returns 200 with updated task
5. **Toggles completion** → Returns 200 with completed=true
6. **Deletes task** → Returns 204, task no longer in list

#### Edge Cases

**Empty Data:**
- List tasks when user has none → Returns 200 with empty array
- Create task with empty title → Returns 400 validation error
- Update task with no fields → Returns 400 validation error

**Invalid IDs:**
- Get task with non-existent ID → Returns 404
- Delete task with non-existent ID → Returns 404
- Access task belonging to different user → Returns 404

**Authentication:**
- Request without token → Returns 401
- Request with expired token → Returns 401
- User ID mismatch → Returns 403

**Rate Limiting:**
- Exceed rate limit → Returns 429 with retry_after

### Performance Requirements

- **List tasks:** < 100ms for up to 1000 tasks
- **Create task:** < 50ms
- **Get task:** < 30ms
- **Update task:** < 50ms
- **Delete task:** < 50ms
- **Toggle completion:** < 50ms

### Load Testing
- Support 100 concurrent users
- Handle 1000 requests/minute across all endpoints
- Maintain < 200ms p95 response time under load

---

## Versioning

**Current Version:** v1
**Versioning Strategy:** URL-based (future: `/api/v2/{user_id}/tasks`)

**Breaking Changes Policy:**
- Version incremented for breaking changes
- Old versions supported for 6 months after new version release
- Deprecation warnings in response headers

---

## Security Considerations

### Authentication
- JWT tokens expire after 24 hours
- Refresh tokens expire after 30 days
- Tokens stored securely (httpOnly cookies recommended)

### Authorization
- All endpoints verify `user_id` matches authenticated user
- Database queries include `WHERE user_id = ?` filter
- No cross-user data access possible

### Input Validation
- All inputs sanitized to prevent SQL injection
- XSS protection via Content-Security-Policy headers
- Request size limited to 1MB

### HTTPS
- All API requests must use HTTPS in production
- HTTP requests redirected to HTTPS
- HSTS headers enabled

---

## Changelog

### v1.0.0 (2025-12-12)
- Initial API specification
- Six core endpoints for task CRUD operations
- JWT-based authentication
- User data isolation
- Rate limiting
- CORS configuration

---

## Support

**Documentation:** See `/specs` directory
**Issues:** GitHub Issues
**Contact:** project-support@example.com

---

**Last Updated:** 2025-12-12
**Status:** Production Ready
**Maintained By:** Development Team
