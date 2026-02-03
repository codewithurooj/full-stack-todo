# Implementation Plan: Intermediate Task Management Features

**Branch**: `009-intermediate-features` | **Date**: 2026-01-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-intermediate-features/spec.md`

## Summary

This feature adds intermediate-level task organization capabilities: priorities (high/medium/low), tags/categories, keyword search, multi-criteria filtering (status, priority, tags, date range), and flexible sorting (due date, priority, creation date, alphabetically). These enhancements transform the basic task list into a powerful organizational tool, enabling users to focus on relevant work and quickly find specific tasks within large lists.

**Technical Approach**: Extend existing Task model with two new database columns (priority VARCHAR, tags TEXT[]), update backend API with query parameters for filtering and sorting, enhance MCP tools to support priority and tags, and build frontend UI components for filter controls, search bar, sort dropdown, and visual priority/tag displays.

## Technical Context

**Language/Version**: Python 3.13+ (backend), TypeScript/Next.js 16+ (frontend)
**Primary Dependencies**: FastAPI 0.100+, SQLModel 0.0.8+, PostgreSQL (Neon), React 18+, Tailwind CSS
**Storage**: PostgreSQL with priority column (indexed) and tags array column
**Testing**: pytest (backend), Jest (frontend), manual E2E testing
**Target Platform**: Web application (desktop and mobile responsive)
**Project Type**: Full-stack web application (monorepo)
**Performance Goals**:
- Search: <1s response for 1000 tasks
- Filter: <1s with result counts
- Sort: <500ms for 1000 tasks
- Tag autocomplete: <200ms

**Constraints**:
- Zero downtime for database migration
- Backward compatible with existing tasks (default priority=medium)
- No breaking changes to existing API endpoints
- Must work with existing AI chatbot/MCP integration

**Scale/Scope**:
- 5 user stories (P1-P4)
- 41 functional requirements
- Database: 2 new columns + 1 index
- Backend: 3 updated endpoints, 3 updated MCP tools
- Frontend: 4 new components (filters, search, tags, sort controls)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Spec-Driven Development
- [x] Feature specified in `/specs/009-intermediate-features/spec.md`
- [x] Spec includes user stories, acceptance criteria, functional requirements
- [x] No manual code writing - will use Claude Code generation

### ✅ Architecture & Technology Stack Alignment
- [x] Frontend: Next.js 16+ (App Router), TypeScript, Tailwind CSS ✓
- [x] Backend: FastAPI, SQLModel, PostgreSQL ✓
- [x] Existing Phase 3 AI chatbot integration maintained
- [x] Existing Phase 4 Docker/Kubernetes deployment unchanged

### ✅ RESTful API Design
- [x] Extends existing `/api/{user_id}/tasks` endpoints with query parameters
- [x] No new endpoints required - adds optional parameters to GET /tasks
- [x] MCP tools updated to support priority and tags parameters
- [x] Maintains stateless design

### ✅ Data Management
- [x] User data isolation: all queries filtered by user_id
- [x] PostgreSQL schema extension (priority + tags columns)
- [x] Index on priority field for performance
- [x] No cross-user data access

### ✅ Security & Authentication
- [x] JWT verification on all endpoints (unchanged)
- [x] User ID validation matches existing patterns
- [x] No new authentication requirements

### ✅ Testing & Quality Assurance
- [x] Backend tests for filtering, sorting, search logic
- [x] Frontend tests for new components
- [x] MCP tool tests for priority/tags parameters
- [x] Manual E2E testing checklist

**Gate Status**: ✅ PASSED - All constitution requirements met, can proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/009-intermediate-features/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (implementation plan)
├── research.md          # Phase 0: Technology decisions (to be created)
├── data-model.md        # Phase 1: Database schema design (to be created)
├── quickstart.md        # Phase 1: Quick implementation guide (to be created)
├── contracts/           # Phase 1: API contracts (to be created)
│   └── tasks-api.md     # Updated API documentation
└── tasks.md             # Phase 2: Task breakdown (created by /sp.tasks command)
```

### Source Code (repository root)

**Backend Changes**:
```text
backend/
├── app/
│   ├── models/
│   │   └── task.py                    # UPDATE: Add priority + tags fields
│   ├── routes/
│   │   └── tasks.py                   # UPDATE: Add query params (priority, tags, search, sort)
│   ├── mcp_server/
│   │   └── tools/
│   │       ├── add_task.py           # UPDATE: Accept priority, tags parameters
│   │       ├── list_tasks.py         # UPDATE: Add filtering/sorting logic
│   │       └── update_task.py        # UPDATE: Accept priority, tags updates
│   └── utils/
│       └── query_builder.py          # NEW: Helper for filter/sort query construction
├── migrations/
│   └── 002_add_priority_tags.sql    # NEW: Database migration
└── tests/
    ├── test_tasks.py                 # UPDATE: Add filter/sort/search tests
    └── test_mcp_tools.py             # UPDATE: Add priority/tags tests
```

**Frontend Changes**:
```text
frontend/
├── app/
│   └── tasks/
│       └── page.tsx                  # UPDATE: Add filter/search/sort UI
├── components/
│   └── tasks/
│       ├── task-item.tsx             # UPDATE: Display priority + tags
│       ├── task-filters.tsx          # UPDATE: Add priority/tag filters
│       ├── search-bar.tsx            # NEW: Search input component
│       ├── sort-dropdown.tsx         # NEW: Sort controls
│       ├── priority-badge.tsx        # NEW: Visual priority indicator
│       ├── tag-input.tsx             # NEW: Tag input with autocomplete
│       └── tag-list.tsx              # NEW: Display task tags
├── lib/
│   └── api.ts                        # UPDATE: Add query params to fetchTasks
└── types/
    └── task.ts                       # UPDATE: Add priority, tags to Task type
```

## Phase 0: Research & Technical Decisions

### 0.1 Database Schema Design

**Decision: PostgreSQL Column Types**
- **Priority**: `VARCHAR(20)` with CHECK constraint for three values
  - Rationale: Simple enumeration, indexed for fast filtering
  - Alternatives: Integer (0,1,2) or ENUM type
  - Choice: VARCHAR is more readable in queries and logs
- **Tags**: `TEXT[]` (PostgreSQL array)
  - Rationale: Native array support, efficient ANY/ALL operators
  - Alternatives: Separate tags table with junction, JSONB array
  - Choice: TEXT[] is simplest, performant for <100 tags per task

**Index Strategy**:
- CREATE INDEX idx_tasks_priority ON tasks(priority) - For priority filters
- Consider GIN index on tags if searching within tags becomes needed
- Existing indexes (user_id, created_at) remain

### 0.2 Query Performance Patterns

**Filtering Logic**:
- Multiple filters use AND logic (FR-022)
- SQLModel query: `select(Task).where(Task.user_id == user_id, Task.priority == 'high', Task.tags.overlap(['work']))`
- PostgreSQL overlap operator for tag filtering: `tags && ARRAY['work', 'personal']`

**Search Implementation**:
- ILIKE operator for case-insensitive partial matching (FR-014, FR-015)
- Query: `WHERE title ILIKE '%keyword%' OR description ILIKE '%keyword%'`
- Consider PostgreSQL full-text search (tsvector) if performance degrades at scale

**Sorting Patterns**:
```sql
-- Priority: Custom order (high, medium, low)
ORDER BY CASE priority
  WHEN 'high' THEN 1
  WHEN 'medium' THEN 2
  WHEN 'low' THEN 3
END

-- Due date: NULLs last
ORDER BY due_date NULLS LAST

-- Alphabetical
ORDER BY LOWER(title)
```

### 0.3 Frontend State Management

**URL Query Parameters for Filters**:
- Persist filter state in URL: `?priority=high&tags=work,urgent&search=meeting&sort=priority`
- React hook: `useSearchParams()` for reading/updating
- Enables shareable filtered views

**Tag Autocomplete**:
- Fetch unique tags from backend: `GET /api/{user_id}/tasks/tags`
- Client-side filtering of suggestions as user types
- Debounce API calls (300ms) to reduce load

### 0.4 MCP Tool Schema Updates

**add_task tool**:
```json
{
  "name": "add_task",
  "parameters": {
    "type": "object",
    "properties": {
      "user_id": {"type": "string"},
      "title": {"type": "string"},
      "description": {"type": "string"},
      "priority": {
        "type": "string",
        "enum": ["high", "medium", "low"],
        "default": "medium"
      },
      "tags": {
        "type": "array",
        "items": {"type": "string"},
        "default": []
      }
    },
    "required": ["user_id", "title"]
  }
}
```

**list_tasks tool**:
```json
{
  "name": "list_tasks",
  "parameters": {
    "properties": {
      "status": {"type": "string", "enum": ["all", "pending", "completed"]},
      "priority": {"type": "string", "enum": ["high", "medium", "low"]},
      "tags": {"type": "array", "items": {"type": "string"}},
      "sort_by": {"type": "string", "enum": ["due_date", "priority", "created_at", "title"]},
      "search": {"type": "string"}
    }
  }
}
```

### 0.5 AI Chatbot Natural Language Processing

**Priority Keyword Mapping** (FR-032):
- "urgent", "important", "critical" → high
- "normal", "regular" → medium
- "low", "minor", "someday" → low

**Tag Extraction** (FR-033):
- Regex pattern: Look for "tag(s)?" or "category/categories" keywords
- Example: "add task with tags work and urgent" → tags=["work", "urgent"]
- Example: "work task" → tags=["work"]

**Filter Intent Recognition** (FR-035):
- "show high priority tasks" → priority=high
- "my work tasks" → tags=["work"]
- "completed tasks" → status=completed
- "tasks from last week" → date_from=[7 days ago]

## Phase 1: Design & Contracts

### 1.1 Data Model

**Entity: Task (Extended)**
```
Task {
  id: Integer (PK)
  user_id: String (FK, indexed)
  title: String (1-200 chars)
  description: String? (0-1000 chars)
  completed: Boolean (default: false)

  // NEW FIELDS
  priority: String (high|medium|low, default: medium)
  tags: String[] (default: [])

  created_at: DateTime
  updated_at: DateTime
}
```

**Validation Rules**:
- priority MUST be one of: 'high', 'medium', 'low'
- tags MUST be array of strings, max 50 tags per task
- Individual tag max length: 50 characters
- Tag names: alphanumeric, hyphens, underscores only

### 1.2 API Contracts

**GET /api/{user_id}/tasks - Updated**

Query Parameters (all optional):
```typescript
{
  priority?: 'high' | 'medium' | 'low'
  tags?: string[]           // Can specify multiple: tags=work&tags=personal
  status?: 'all' | 'pending' | 'completed'
  search?: string           // Keyword search in title/description
  sort_by?: 'due_date' | 'priority' | 'created_at' | 'title'
  sort_order?: 'asc' | 'desc'
  date_from?: string        // ISO 8601 date
  date_to?: string          // ISO 8601 date
}
```

Response:
```typescript
{
  tasks: Task[]
  count: number            // Total matching tasks
  filters_applied: {       // Echo of active filters
    priority?: string
    tags?: string[]
    status?: string
    search?: string
    sort_by?: string
  }
}
```

**POST /api/{user_id}/tasks - Updated**

Request Body:
```typescript
{
  title: string           // Required, 1-200 chars
  description?: string    // Optional, 0-1000 chars
  priority?: 'high' | 'medium' | 'low'  // Optional, default: medium
  tags?: string[]         // Optional, default: []
}
```

**PUT /api/{user_id}/tasks/{task_id} - Updated**

Request Body (all fields optional):
```typescript
{
  title?: string
  description?: string
  completed?: boolean
  priority?: 'high' | 'medium' | 'low'
  tags?: string[]         // Replaces existing tags
}
```

**GET /api/{user_id}/tasks/tags - New**

Returns unique tags used by user:
```typescript
{
  tags: string[]          // Sorted alphabetically
  usage_count: Record<string, number>  // Tag → count mapping
}
```

### 1.3 Database Migration

**File: `backend/migrations/002_add_priority_tags.sql`**

```sql
-- Migration: Add priority and tags to tasks table
-- Date: 2026-01-07
-- Feature: 009-intermediate-features

BEGIN;

-- Step 1: Add priority column with default
ALTER TABLE tasks
  ADD COLUMN priority VARCHAR(20) DEFAULT 'medium';

-- Step 2: Add tags column with default
ALTER TABLE tasks
  ADD COLUMN tags TEXT[] DEFAULT '{}';

-- Step 3: Add check constraint for priority
ALTER TABLE tasks
  ADD CONSTRAINT chk_tasks_priority
  CHECK (priority IN ('high', 'medium', 'low'));

-- Step 4: Create index on priority for filtering performance
CREATE INDEX idx_tasks_priority ON tasks(priority);

-- Step 5: Verify migration
DO $$
BEGIN
  ASSERT (SELECT COUNT(*) FROM information_schema.columns
          WHERE table_name = 'tasks' AND column_name = 'priority') = 1;
  ASSERT (SELECT COUNT(*) FROM information_schema.columns
          WHERE table_name = 'tasks' AND column_name = 'tags') = 1;
  ASSERT (SELECT COUNT(*) FROM pg_indexes
          WHERE tablename = 'tasks' AND indexname = 'idx_tasks_priority') = 1;
  RAISE NOTICE 'Migration verified successfully';
END $$;

COMMIT;
```

**Rollback: `backend/migrations/002_add_priority_tags_rollback.sql`**

```sql
BEGIN;

DROP INDEX IF EXISTS idx_tasks_priority;
ALTER TABLE tasks DROP COLUMN IF EXISTS priority;
ALTER TABLE tasks DROP COLUMN IF EXISTS tags;

COMMIT;
```

### 1.4 Backend Implementation Pattern

**SQLModel Update**:
```python
# backend/app/models/task.py
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import ARRAY, String

class TaskBase(SQLModel):
    title: str
    description: Optional[str] = None
    completed: bool = False
    priority: str = Field(default="medium", regex="^(high|medium|low)$")
    tags: List[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))

class Task(TaskBase, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
```

**Query Builder Helper**:
```python
# backend/app/utils/query_builder.py
from sqlmodel import select, Session
from typing import Optional, List
from app.models.task import Task

def build_tasks_query(
    user_id: str,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    """Build filtered and sorted tasks query"""
    query = select(Task).where(Task.user_id == user_id)

    # Apply filters
    if priority:
        query = query.where(Task.priority == priority)

    if tags:
        # PostgreSQL overlap operator for array matching
        query = query.where(Task.tags.overlap(tags))

    if status == "completed":
        query = query.where(Task.completed == True)
    elif status == "pending":
        query = query.where(Task.completed == False)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Task.title.ilike(search_pattern)) |
            (Task.description.ilike(search_pattern))
        )

    # Apply sorting
    if sort_by == "priority":
        # Custom order: high > medium > low
        query = query.order_by(
            case(
                (Task.priority == 'high', 1),
                (Task.priority == 'medium', 2),
                (Task.priority == 'low', 3)
            )
        )
    elif sort_by == "title":
        query = query.order_by(Task.title.asc() if sort_order == "asc" else Task.title.desc())
    elif sort_by == "created_at":
        query = query.order_by(Task.created_at.asc() if sort_order == "asc" else Task.created_at.desc())

    return query
```

### 1.5 Frontend Component Patterns

**Priority Badge Component**:
```typescript
// frontend/components/tasks/priority-badge.tsx
const PRIORITY_STYLES = {
  high: 'bg-red-100 text-red-800 border-red-300',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  low: 'bg-green-100 text-green-800 border-green-300',
}

export function PriorityBadge({ priority }: { priority: string }) {
  return (
    <span className={`px-2 py-1 text-xs font-medium rounded border ${PRIORITY_STYLES[priority]}`}>
      {priority}
    </span>
  )
}
```

**Tag Input with Autocomplete**:
```typescript
// frontend/components/tasks/tag-input.tsx
export function TagInput({
  value,
  onChange,
  suggestions
}: {
  value: string[],
  onChange: (tags: string[]) => void,
  suggestions: string[]
}) {
  const [input, setInput] = useState('')
  const [filteredSuggestions, setFilteredSuggestions] = useState<string[]>([])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setInput(val)

    if (val.length > 0) {
      setFilteredSuggestions(
        suggestions.filter(s =>
          s.toLowerCase().includes(val.toLowerCase()) &&
          !value.includes(s)
        )
      )
    } else {
      setFilteredSuggestions([])
    }
  }

  const addTag = (tag: string) => {
    if (tag && !value.includes(tag)) {
      onChange([...value, tag])
      setInput('')
      setFilteredSuggestions([])
    }
  }

  // ... render input + suggestion dropdown + tag pills
}
```

**Filter Panel Component**:
```typescript
// frontend/components/tasks/task-filters.tsx
export function TaskFilters({
  filters,
  onFilterChange,
  availableTags
}: FilterProps) {
  return (
    <div className="flex gap-4 p-4 bg-gray-50 rounded-lg">
      {/* Priority filter */}
      <select
        value={filters.priority || 'all'}
        onChange={(e) => onFilterChange('priority', e.target.value)}
      >
        <option value="all">All Priorities</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
      </select>

      {/* Tag filter */}
      <TagSelector
        selected={filters.tags || []}
        options={availableTags}
        onChange={(tags) => onFilterChange('tags', tags)}
      />

      {/* Status filter */}
      <select
        value={filters.status || 'all'}
        onChange={(e) => onFilterChange('status', e.target.value)}
      >
        <option value="all">All Tasks</option>
        <option value="pending">Pending</option>
        <option value="completed">Completed</option>
      </select>

      {/* Clear filters */}
      <button onClick={() => onFilterChange('clear')}>Clear All</button>
    </div>
  )
}
```

## Phase 2: Implementation Checklist

*Note: Detailed task breakdown will be generated by `/sp.tasks` command.*

### Database
- [ ] Create migration files (forward + rollback)
- [ ] Test migration on local database
- [ ] Apply migration to development database
- [ ] Verify indexes created successfully

### Backend Models
- [ ] Update Task model with priority and tags fields
- [ ] Update TaskCreate schema
- [ ] Update TaskUpdate schema
- [ ] Update TaskRead schema
- [ ] Add validation for priority enum
- [ ] Add validation for tags array

### Backend API Routes
- [ ] Update GET /tasks with query parameters
- [ ] Add filtering logic (priority, tags, status)
- [ ] Add search logic (title + description)
- [ ] Add sorting logic (4 sort options)
- [ ] Add GET /tasks/tags endpoint
- [ ] Update POST /tasks to accept priority + tags
- [ ] Update PUT /tasks/{id} to update priority + tags
- [ ] Test all query parameter combinations

### Backend MCP Tools
- [ ] Update add_task tool schema + handler
- [ ] Update list_tasks tool schema + handler
- [ ] Update update_task tool schema + handler
- [ ] Add NLP for priority keyword mapping
- [ ] Add NLP for tag extraction
- [ ] Test chatbot with priority/tags commands

### Frontend Components
- [ ] Create PriorityBadge component
- [ ] Create TagInput component with autocomplete
- [ ] Create TagList display component
- [ ] Update TaskItem to show priority + tags
- [ ] Create SearchBar component
- [ ] Create SortDropdown component
- [ ] Update TaskFilters with priority + tags
- [ ] Add URL query param state management

### Frontend Pages
- [ ] Update tasks page with filter/search/sort UI
- [ ] Update create task form with priority + tags
- [ ] Update edit task form with priority + tags
- [ ] Add filter state persistence in URL
- [ ] Fetch available tags for autocomplete

### Testing
- [ ] Backend: Test priority filtering
- [ ] Backend: Test tag filtering
- [ ] Backend: Test combined filters
- [ ] Backend: Test search functionality
- [ ] Backend: Test sorting options
- [ ] Backend: Test MCP tools with new params
- [ ] Frontend: Test filter UI interactions
- [ ] Frontend: Test tag autocomplete
- [ ] Frontend: Test priority badge display
- [ ] E2E: Complete user flow with all features

### Documentation
- [ ] Update API documentation
- [ ] Update MCP tool documentation
- [ ] Add examples to quickstart guide
- [ ] Update README with new features

## Dependencies & Risks

### External Dependencies
- PostgreSQL array support (built-in, no risk)
- SQLModel ARRAY column type (supported, no risk)
- Next.js useSearchParams hook (stable, no risk)

### Technical Risks
1. **Database Migration**: Zero-downtime required
   - Mitigation: Use default values, backfill not needed
   - Impact: Low - new columns nullable or have defaults

2. **Query Performance**: Complex filters on large datasets
   - Mitigation: Index on priority, consider GIN index for tags
   - Impact: Medium - monitor query times, optimize if needed

3. **Tag Autocomplete**: Too many unique tags
   - Mitigation: Limit suggestions to 50, cache results
   - Impact: Low - pagination or search within tags

4. **AI Chatbot NLP**: Ambiguous priority/tag extraction
   - Mitigation: Provide examples, fallback to defaults
   - Impact: Low - users can manually correct

### Integration Points
- Existing Phase 3 AI chatbot: Update MCP tool schemas
- Existing Phase 4 Docker/K8s: No changes needed
- Existing auth system: No changes needed

## Success Metrics

*Measured after implementation*

- [ ] Search returns results in <1 second (SC-003)
- [ ] Filter operations complete in <1 second (SC-004)
- [ ] Sort operations complete in <500ms (SC-005)
- [ ] Users can assign priority in <3 seconds (SC-001)
- [ ] Users can add tags in <5 seconds (SC-002)
- [ ] All 41 functional requirements tested and passing
- [ ] All 25 acceptance scenarios verified
- [ ] Chatbot correctly interprets 95% of priority/tag requests (SC-009)

## Next Steps

After this plan is approved:

1. **Run `/sp.tasks`** to generate detailed task breakdown
2. **Run `/sp.implement`** to execute implementation
3. **Use custom agents** to accelerate development:
   - `db-migrator` agent for database migration
   - `helm-updater` agent to update Kubernetes configs if needed
4. **Run `/sp.phr`** to document implementation

---

**Plan Status**: ✅ Complete - Ready for task generation
**Estimated Effort**: 2-3 days (12-18 hours)
**Complexity**: Medium (database migration + UI + MCP updates)
