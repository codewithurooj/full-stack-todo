# Validation Quick Reference

## Validation Rules

### Priority
```python
# Valid values (case-sensitive)
"high"
"medium"
"low"

# Backend: validate_priority(priority: str)
# Frontend: Dropdown enforces valid values
```

### Tags
```python
# Rules
- Max 50 tags per task
- Each tag max 50 characters
- Alphanumeric, hyphens, underscores only: ^[a-zA-Z0-9_-]+$
- Cannot be empty
- Case-insensitive (normalized to lowercase)

# Backend: validate_tags(tags: List[str])
# Frontend: TagInput component with real-time validation
```

### Date Range
```python
# Format
ISO 8601: "2024-01-15T00:00:00Z"

# Rules
- date_from must be <= date_to
- Both optional
- Handles timezone (Z suffix)

# Backend: validate_date_range(date_from, date_to)
# Frontend: Date inputs with format validation
```

## Error Messages

### Priority Errors
```
Invalid priority. Must be one of: high, medium, low
```

### Tag Errors
```
Tag cannot be empty
Tag 'example' exceeds maximum length of 50 characters
Tag 'example@' contains invalid characters. Only alphanumeric, hyphens, and underscores allowed
Maximum 50 tags allowed. Received 51 tags
```

### Date Range Errors
```
Invalid date_from format: '2024-13-01'. Must be ISO 8601 format (e.g., '2024-01-15T00:00:00Z')
Invalid date range: date_from (2024-12-31) must be before or equal to date_to (2024-01-01)
```

## API Response Codes

- `200 OK` - Success
- `201 Created` - Task created
- `204 No Content` - Task deleted
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing/invalid token
- `403 Forbidden` - User ID mismatch
- `404 Not Found` - Task not found

## Client-Side Validation

### Before API Call
```typescript
// Title
if (title.trim().length === 0) return "Title required"
if (title.length > 200) return "Title too long"

// Description
if (description.length > 1000) return "Description too long"

// Tags
if (tags.length > 50) return "Too many tags"
for (const tag of tags) {
  if (tag.length > 50) return "Tag too long"
  if (!/^[\w-]+$/.test(tag)) return "Invalid tag format"
}
```

### Tag Input Component
```typescript
// Real-time validation
const isValidTag = (tag: string) => {
  return tag.length <= 50 && /^[\w-]+$/.test(tag)
}
```

## Logging

### Backend Logs

**Filter operations:**
```
INFO: list_tasks: user=user123, filters={'priority': 'high'}, result_count=5
WARN: list_tasks validation error: user=user123, error=Invalid priority
```

**Task operations:**
```
INFO: create_task: user=user123, task_id=42, priority=high, tags_count=3
INFO: update_task: user=user123, task_id=42, updated_fields=['priority']
```

## Testing

Run validation tests:
```bash
cd backend
python test_validation.py
```

Expected output: All ✓ (28 test cases)

## Common Issues

### "Invalid priority" error
- Check case: must be lowercase ("high", not "HIGH")
- Check spelling: "medium" not "normal"

### "Tag contains invalid characters"
- Remove spaces: "my tag" → "my-tag"
- Remove special chars: "task@home" → "task-home"
- Use hyphens or underscores: "work_urgent" or "work-urgent"

### "Invalid date range"
- Check format: Use ISO 8601 with Z suffix
- Check order: date_from must be before date_to
- Check values: Valid year/month/day

## File Locations

### Backend
- `backend/app/utils/validation.py` - Validation functions
- `backend/app/routes/tasks.py` - Route handlers with validation
- `backend/test_validation.py` - Test suite

### Frontend
- `frontend/lib/api/client.ts` - API client with error handling
- `frontend/components/tasks/create-task-form.tsx` - Create form validation
- `frontend/components/tasks/edit-task-form.tsx` - Edit form validation
- `frontend/components/tasks/tag-input.tsx` - Tag input validation
- `frontend/components/ui/validation-error.tsx` - Error display component
- `frontend/components/tasks/empty-state.tsx` - Empty state component

## Example Usage

### Backend (FastAPI)
```python
from app.utils.validation import validate_priority, validate_tags

# In endpoint
try:
    if priority:
        validate_priority(priority)
    if tags:
        validate_tags(tags)
except HTTPException as e:
    logger.warning(f"Validation error: {e.detail}")
    raise
```

### Frontend (React)
```typescript
import { ApiError } from '@/lib/api/client'

try {
  await taskApi.create(userId, taskData)
} catch (err) {
  if (err instanceof ApiError) {
    setError(err.message)
  }
}
```

## Edge Cases Handled

- Empty tag arrays → Valid (no tags)
- Null date ranges → Valid (no date filter)
- Exactly 50 tags → Valid (boundary)
- Exactly 50 char tag → Valid (boundary)
- 51 tags → Invalid (exceeds limit)
- 51 char tag → Invalid (exceeds limit)
- Reversed date range → Invalid (logical error)
- Invalid ISO date → Invalid (format error)

---

**Last Updated**: 2026-01-08
**Feature**: 009-intermediate-features
**Status**: Complete
