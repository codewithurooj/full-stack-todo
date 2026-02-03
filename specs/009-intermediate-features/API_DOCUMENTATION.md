# API Documentation: Intermediate Task Management Features

**Feature**: 009-intermediate-features
**Version**: 1.0.0
**Last Updated**: 2026-01-08

## Overview

This document describes the API endpoints and parameters for the intermediate task management features: priorities, tags, search, filtering, and sorting.

---

## Endpoints

### 1. List Tasks with Filters

**Endpoint**: `GET /api/{user_id}/tasks`

**Description**: Retrieve tasks with optional filtering, searching, and sorting.

**Path Parameters**:
- `user_id` (string, required): JWT user ID

**Query Parameters** (all optional):

| Parameter | Type | Default | Description | Example |
|-----------|------|---------|-------------|---------|
| `priority` | string | - | Filter by priority (high\|medium\|low) | `?priority=high` |
| `tags` | string[] | - | Filter by tags (multiple allowed) | `?tags=work&tags=urgent` |
| `status` | string | "all" | Filter by completion (all\|pending\|completed) | `?status=pending` |
| `search` | string | - | Keyword search in title/description | `?search=meeting` |
| `sort_by` | string | "created_at" | Sort field (priority\|created_at\|title) | `?sort_by=priority` |
| `sort_order` | string | "desc" | Sort direction (asc\|desc) | `?sort_order=asc` |
| `date_from` | string | - | Filter by creation date (ISO 8601) | `?date_from=2024-01-01` |
| `date_to` | string | - | Filter by creation date (ISO 8601) | `?date_to=2024-12-31` |

**Response** (200 OK):
```json
{
  "tasks": [
    {
      "id": 123,
      "user_id": "user-abc",
      "title": "Complete project",
      "description": "Finish the implementation",
      "completed": false,
      "priority": "high",
      "tags": ["work", "urgent"],
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 1,
  "filters_applied": {
    "priority": "high",
    "tags": ["work"],
    "status": "all",
    "search": null,
    "sort_by": "created_at",
    "sort_order": "desc"
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid query parameters
- `401 Unauthorized`: Missing or invalid JWT token
- `500 Internal Server Error`: Server error

**Examples**:

```bash
# Get all high priority tasks
GET /api/user123/tasks?priority=high

# Get work-related tasks sorted by priority
GET /api/user123/tasks?tags=work&sort_by=priority

# Search for meeting tasks
GET /api/user123/tasks?search=meeting

# Complex filter
GET /api/user123/tasks?priority=high&tags=work&status=pending&sort_by=priority&sort_order=asc
```

---

### 2. Create Task

**Endpoint**: `POST /api/{user_id}/tasks`

**Description**: Create a new task with priority and tags.

**Path Parameters**:
- `user_id` (string, required): JWT user ID

**Request Body**:
```json
{
  "title": "Complete project",
  "description": "Finish the implementation",
  "priority": "high",
  "tags": ["work", "urgent"]
}
```

**Field Specifications**:
- `title` (string, required): Task title (1-200 characters)
- `description` (string, optional): Task description (0-1000 characters)
- `priority` (string, optional): Priority level - must be "high", "medium", or "low" (default: "medium")
- `tags` (string[], optional): Array of tags (max 50 tags, each max 50 chars, alphanumeric/hyphens/underscores only)

**Response** (201 Created):
```json
{
  "id": 123,
  "user_id": "user-abc",
  "title": "Complete project",
  "description": "Finish the implementation",
  "completed": false,
  "priority": "high",
  "tags": ["work", "urgent"],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Validation error (invalid priority, tags, or required fields missing)
- `401 Unauthorized`: Missing or invalid JWT token
- `500 Internal Server Error`: Server error

**Validation Rules**:
- Priority: Must be "high", "medium", or "low" (case-sensitive, lowercase)
- Tags: Alphanumeric, hyphens, underscores only (regex: `^[\w-]+$`)
- Max 50 tags per task
- Each tag max 50 characters
- Tag names normalized to lowercase

---

### 3. Update Task

**Endpoint**: `PUT /api/{user_id}/tasks/{task_id}`

**Description**: Update an existing task (all fields optional).

**Path Parameters**:
- `user_id` (string, required): JWT user ID
- `task_id` (integer, required): Task ID

**Request Body** (all fields optional):
```json
{
  "title": "Updated title",
  "description": "Updated description",
  "completed": true,
  "priority": "medium",
  "tags": ["work", "done"]
}
```

**Response** (200 OK):
```json
{
  "id": 123,
  "user_id": "user-abc",
  "title": "Updated title",
  "description": "Updated description",
  "completed": true,
  "priority": "medium",
  "tags": ["work", "done"],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T15:45:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Validation error
- `401 Unauthorized`: Missing or invalid JWT token
- `404 Not Found`: Task not found or not owned by user
- `500 Internal Server Error`: Server error

**Important Notes**:
- Tags parameter **replaces** existing tags (not merge)
- To clear tags, send empty array: `{"tags": []}`
- To clear priority, send default: `{"priority": "medium"}`

---

### 4. Get Unique Tags

**Endpoint**: `GET /api/{user_id}/tasks/tags`

**Description**: Get all unique tags used by the user for autocomplete.

**Path Parameters**:
- `user_id` (string, required): JWT user ID

**Response** (200 OK):
```json
{
  "tags": ["done", "personal", "urgent", "work"],
  "usage_count": {
    "work": 15,
    "urgent": 8,
    "personal": 5,
    "done": 3
  }
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid JWT token
- `500 Internal Server Error`: Server error

**Notes**:
- Tags are sorted alphabetically
- Usage count shows how many tasks have each tag
- Useful for tag autocomplete in frontend

---

### 5. Delete Task

**Endpoint**: `DELETE /api/{user_id}/tasks/{task_id}`

**Description**: Delete a task (existing endpoint, unchanged).

**Path Parameters**:
- `user_id` (string, required): JWT user ID
- `task_id` (integer, required): Task ID

**Response** (200 OK):
```json
{
  "message": "Task deleted successfully"
}
```

---

### 6. Toggle Task Completion

**Endpoint**: `PATCH /api/{user_id}/tasks/{task_id}/complete`

**Description**: Toggle task completion status (existing endpoint, unchanged).

**Path Parameters**:
- `user_id` (string, required): JWT user ID
- `task_id` (integer, required): Task ID

**Response** (200 OK):
```json
{
  "id": 123,
  "user_id": "user-abc",
  "title": "Complete project",
  "description": "Finish the implementation",
  "completed": true,
  "priority": "high",
  "tags": ["work", "urgent"],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T16:00:00Z"
}
```

---

## Filter Logic

### Multiple Filters (AND Logic)
When multiple filters are applied, they are combined with AND logic:

```bash
# Returns tasks that are:
# - High priority AND
# - Tagged with "work" AND
# - Pending (not completed)
GET /api/user123/tasks?priority=high&tags=work&status=pending
```

### Tag Filtering (OR Logic)
When multiple tags are specified, tasks matching ANY of the tags are returned:

```bash
# Returns tasks tagged with "work" OR "personal"
GET /api/user123/tasks?tags=work&tags=personal
```

### Search Logic
Search uses case-insensitive ILIKE matching on both title and description:

```bash
# Returns tasks where title OR description contains "meeting"
GET /api/user123/tasks?search=meeting
```

---

## Sorting

### Sort Fields

| Value | Description | Sort Order |
|-------|-------------|------------|
| `priority` | Priority level | high → medium → low |
| `created_at` | Creation date | Newest/oldest first |
| `title` | Alphabetical | A-Z or Z-A |

### Sort Order

| Value | Description |
|-------|-------------|
| `asc` | Ascending (A-Z, oldest first, low to high) |
| `desc` | Descending (Z-A, newest first, high to low) |

### Examples

```bash
# High priority tasks first
GET /api/user123/tasks?sort_by=priority&sort_order=asc

# Newest tasks first (default)
GET /api/user123/tasks?sort_by=created_at&sort_order=desc

# Alphabetical A-Z
GET /api/user123/tasks?sort_by=title&sort_order=asc
```

---

## Validation Rules

### Priority
- **Valid values**: "high", "medium", "low"
- **Case-sensitive**: Must be lowercase
- **Default**: "medium"
- **Example error**: `"Invalid priority value. Must be one of: high, medium, low"`

### Tags
- **Format**: Alphanumeric, hyphens, underscores only
- **Regex**: `^[\w-]+$`
- **Max count**: 50 tags per task
- **Max length**: 50 characters per tag
- **Normalization**: Converted to lowercase, deduplicated, sorted
- **Example errors**:
  - `"Tag 'hello world' is invalid. Only alphanumeric characters, hyphens, and underscores are allowed."`
  - `"Too many tags. Maximum 50 tags allowed per task."`
  - `"Tag 'verylongnameexceedingfiftycharacterslimitfortagvalidation' exceeds maximum length of 50 characters."`

### Date Ranges
- **Format**: ISO 8601 (e.g., "2024-01-15T00:00:00Z")
- **Validation**: `date_from` must be ≤ `date_to`
- **Example error**: `"date_from must be less than or equal to date_to"`

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Invalid priority value. Must be one of: high, medium, low"
}
```

### Common Error Codes

| Status | Meaning | Common Causes |
|--------|---------|---------------|
| 400 | Bad Request | Invalid parameters, validation errors |
| 401 | Unauthorized | Missing/invalid JWT token |
| 404 | Not Found | Task doesn't exist or not owned by user |
| 422 | Unprocessable Entity | Invalid request body format |
| 500 | Internal Server Error | Database error, unexpected exception |

---

## Performance Considerations

### Database Indexes
- Index on `priority` column for fast filtering
- Index on `user_id` for data isolation
- Index on `created_at` for sorting

### Query Optimization
- Use PostgreSQL ARRAY overlap operator for tag filtering (efficient)
- ILIKE search is case-insensitive but slower than exact match
- Recommend limiting result sets with pagination (not yet implemented)

### Response Times (Target)
- Search: < 1 second for 1000 tasks
- Filter: < 1 second with result counts
- Sort: < 500ms for 1000 tasks
- Tag autocomplete: < 200ms

---

## Backward Compatibility

All new query parameters are **optional**. Existing API calls continue to work:

```bash
# Old API call (still works)
GET /api/user123/tasks

# Response includes new fields but maintains structure
{
  "tasks": [...],  # Now includes priority and tags
  "count": 10
}
```

---

## MCP Tools Integration

The MCP tools (`add_task`, `list_tasks`, `update_task`) support the same parameters and validation rules as the REST API.

See `backend/app/mcp_server/README.md` for MCP-specific documentation.

---

## Examples

### Complete Workflow

```bash
# 1. Create high priority work task
POST /api/user123/tasks
{
  "title": "Complete Q1 report",
  "priority": "high",
  "tags": ["work", "reports", "q1"]
}

# 2. Get all unique tags
GET /api/user123/tasks/tags
# Returns: ["q1", "reports", "work"]

# 3. Filter high priority work tasks
GET /api/user123/tasks?priority=high&tags=work&sort_by=priority

# 4. Search for reports
GET /api/user123/tasks?search=report

# 5. Update task priority
PUT /api/user123/tasks/123
{
  "priority": "medium"
}

# 6. Mark as complete
PATCH /api/user123/tasks/123/complete
```

---

## Testing

### cURL Examples

```bash
# Create task with tags
curl -X POST http://localhost:8000/api/user123/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "title": "Test task",
    "priority": "high",
    "tags": ["test", "demo"]
  }'

# Get filtered tasks
curl -X GET "http://localhost:8000/api/user123/tasks?priority=high&tags=work" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get available tags
curl -X GET http://localhost:8000/api/user123/tasks/tags \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Changelog

### Version 1.0.0 (2026-01-08)
- Added `priority` field to tasks
- Added `tags` array field to tasks
- Added filtering by priority, tags, status
- Added keyword search in title/description
- Added sorting by priority, created_at, title
- Added date range filtering
- Added GET /tasks/tags endpoint for autocomplete
- Enhanced validation with detailed error messages

---

## Support

For issues or questions:
- GitHub Issues: [repository/issues](https://github.com/your-repo/issues)
- Specification: `specs/009-intermediate-features/spec.md`
- Implementation Plan: `specs/009-intermediate-features/plan.md`
