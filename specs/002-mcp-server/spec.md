# Feature Specification: MCP Server with 5 Custom Tools

**Feature Branch**: `002-mcp-server`
**Created**: 2025-12-27
**Status**: Draft
**Input**: User description: "Create MCP server with these tools: 1. add_task - Create new task, 2. list_tasks - Get all user tasks, 3. complete_task - Toggle task completion, 4. delete_task - Remove task, 5. update_task - Modify task details"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI-Assisted Task Creation (Priority: P1)

As a user having a conversation with the AI assistant, I want the assistant to create tasks on my behalf when I mention things I need to do, so that I don't have to manually switch to the task management interface.

**Why this priority**: Core value proposition of AI-powered task management. Creates immediate value by reducing friction in task capture. Without this, the MCP server provides no functional benefit.

**Independent Test**: Can be fully tested by saying "I need to buy groceries" to the AI assistant and verifying a task appears in the task list. Delivers standalone value even without other tools.

**Acceptance Scenarios**:

1. **Given** I'm chatting with the AI assistant, **When** I say "I need to buy groceries for dinner tonight", **Then** the assistant creates a task titled "Buy groceries for dinner tonight" and confirms the creation
2. **Given** I'm chatting with the AI and have existing tasks, **When** I say "Add a task to finish the report with details about quarterly metrics", **Then** the assistant creates a task with both title and description populated
3. **Given** I try to create a task through the AI, **When** I provide a title exceeding 200 characters, **Then** the assistant explains the title must be shorter and asks me to rephrase

---

### User Story 2 - Conversational Task Viewing (Priority: P1)

As a user, I want to ask the AI assistant "What tasks do I have?" and get a natural language summary of my current tasks, so that I can review my workload without navigating to a separate interface.

**Why this priority**: Essential companion to task creation (P1). Users need to see what they've created to verify and plan. Together with US1, forms minimal viable AI task assistant.

**Independent Test**: Can be tested by asking "What are my pending tasks?" and verifying the assistant retrieves and describes the current task list. Works even if all tasks were created manually (not via AI).

**Acceptance Scenarios**:

1. **Given** I have 3 pending tasks and 2 completed tasks, **When** I ask "What tasks do I have?", **Then** the assistant lists all 5 tasks organized by status
2. **Given** I have 10 tasks, **When** I ask "Show me only my incomplete tasks", **Then** the assistant displays only the 5 pending tasks
3. **Given** I have no tasks, **When** I ask "What's on my todo list?", **Then** the assistant responds that I have no tasks and offers to help create some

---

### User Story 3 - Natural Language Task Completion (Priority: P2)

As a user, I want to tell the AI assistant "Mark 'buy groceries' as done" and have it toggle the task's completion status, so that I can manage task progress through conversation instead of clicking checkboxes.

**Why this priority**: Improves user experience but not essential for MVP. Users can manually toggle completion in the UI. Adds convenience but doesn't enable fundamentally new capability.

**Independent Test**: Can be tested by creating a task manually, then telling the AI to complete it, and verifying the status changes. Demonstrates AI-powered task management without requiring other AI features.

**Acceptance Scenarios**:

1. **Given** I have a pending task "Buy groceries", **When** I say "I finished buying groceries", **Then** the assistant marks that task as complete and confirms it
2. **Given** I have a completed task "Deploy app", **When** I say "Actually I need to redo the deployment", **Then** the assistant marks the task as incomplete again
3. **Given** I have multiple tasks with similar names, **When** I say "Complete the grocery task", **Then** the assistant asks for clarification about which specific task I mean


---

### User Story 4 - Conversational Task Updates (Priority: P2)

As a user, I want to tell the AI "Change the 'buy groceries' task to 'buy groceries and cook dinner'" and have it update the task title, so that I can refine my tasks through natural conversation.

**Why this priority**: Nice-to-have enhancement. Users can manually edit tasks in the UI. Provides convenience but not critical for AI task management value proposition.

**Independent Test**: Can be tested by creating a task, then asking the AI to modify its title or description, and verifying the changes persist. Works independently of other AI features.

**Acceptance Scenarios**:

1. **Given** I have a task titled "Buy groceries", **When** I say "Update that task to include cooking dinner", **Then** the assistant modifies the task title to "Buy groceries and cook dinner"
2. **Given** I have a task without description, **When** I say "Add details: milk, eggs, and bread to the grocery task", **Then** the assistant adds that description to the task

---

### User Story 5 - AI-Powered Task Deletion (Priority: P3)

As a user, I want to tell the AI "Delete the grocery task" and have it permanently remove the task, so that I can clean up my task list through conversation.

**Why this priority**: Lowest priority since deletion is less frequent, potentially destructive, and easily accomplished in the UI.

**Independent Test**: Can be tested by creating a task manually, asking the AI to delete it, and verifying it's removed from the task list.

**Acceptance Scenarios**:

1. **Given** I have a task "Buy groceries", **When** I say "Delete the grocery task", **Then** the assistant removes the task and confirms deletion
2. **Given** I have multiple tasks, **When** I say "Remove all my completed tasks", **Then** the assistant asks for confirmation before deleting multiple tasks

---

### Edge Cases

- What happens when a user asks to create a task but their message doesn't contain a clear task title? (AI should ask for clarification)
- How does the system handle requests to modify tasks that no longer exist? (Return not found error, AI explains task was deleted)
- What happens if a user tries to create 100 tasks rapidly through the AI? (Rate limiting kicks in, AI explains temporary limit)
- How does the AI handle ambiguous references like "complete that task" when multiple pending tasks exist? (AI asks user to specify which task)
- What happens when a user asks to update a task to have an empty title? (Validation fails, AI explains title is required)
- How does the system behave if the database is unavailable when the AI tries to create a task? (Returns database error, AI suggests trying again)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an add_task tool that creates tasks with title (required, 1-200 chars) and optional description (max 1000 chars)
- **FR-002**: System MUST provide a list_tasks tool that retrieves all tasks for authenticated user with optional filtering by completion status
- **FR-003**: System MUST provide a complete_task tool that toggles completion status of existing task
- **FR-004**: System MUST provide an update_task tool that allows modifying task title and/or description
- **FR-005**: System MUST provide a delete_task tool that permanently removes task
- **FR-006**: System MUST enforce user isolation by requiring user_id parameter and verifying it matches authenticated user from JWT token
- **FR-007**: System MUST validate all tool inputs and return clear error messages for validation failures
- **FR-008**: System MUST prevent cross-user data access by including user_id filters in all database queries
- **FR-009**: System MUST sanitize text inputs to prevent XSS attacks
- **FR-010**: System MUST return complete task object after create, update, complete, and delete operations
- **FR-011**: list_tasks tool MUST support sorting by creation date, update date, or title in ascending or descending order
- **FR-012**: System MUST update updated_at timestamp whenever task is modified
- **FR-013**: System MUST return standardized error responses with error code, message, and timestamp
- **FR-014**: System MUST validate task_id format (UUID) before database operations
- **FR-015**: System MUST limit API requests to prevent abuse (100 creates/hour, 200 updates/hour, 1000 reads/hour per user)

### Key Entities

- **MCP Tool**: Programmatic interface that AI agent calls to perform task operations. Each tool has unique name, parameters, return structure, and error handling.
- **Tool Request**: Input data structure containing user_id, tool-specific parameters, and JWT authentication token.
- **Tool Response**: Output data structure containing success data or error information with timestamp.
- **Tool Error**: Categorized failure state (ValidationError, AuthorizationError, NotFoundError, DatabaseError) with HTTP status code mapping.


## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: AI assistant successfully creates tasks through MCP tool calls with 99.9% success rate for valid inputs
- **SC-002**: AI assistant retrieves and presents task lists within 200ms at 95th percentile response time
- **SC-003**: System correctly enforces user isolation with 100% prevention of cross-user data access (zero data leakage)
- **SC-004**: All 5 tools respond to requests within 100ms at 95th percentile under normal load (< 100 concurrent users)
- **SC-005**: System successfully validates all inputs and returns actionable error messages for 100% of invalid requests
- **SC-006**: MCP server handles at least 1000 concurrent tool requests without degradation
- **SC-007**: Task operations through MCP tools match manual UI operations with 100% data consistency
- **SC-008**: System prevents unauthorized access with 100% authentication verification for all tool calls
- **SC-009**: All tool calls are logged with user_id, timestamp, and operation type for audit trail (100% coverage)
- **SC-010**: Rate limiting prevents abuse without impacting legitimate usage (< 1% false positives)

## Out of Scope *(optional)*

The following are explicitly NOT included:

- Batch operations (creating/updating/deleting multiple tasks in one call)
- Task sharing or collaboration
- Task prioritization levels
- Task categories, tags, or project groupings
- Due dates, deadlines, or reminders
- Subtasks or hierarchical structures
- Task edit history or audit trails
- Rich text or formatted descriptions
- File attachments or media
- Full-text search across tasks
- Undo/redo operations
- Task templates or recurring tasks
- Custom fields or metadata
- Analytics or productivity metrics
- Webhooks or real-time notifications
- GraphQL interface
- Advanced NLP for entity extraction

## Assumptions *(optional)*

- JWT authentication already implemented and functional
- Tasks table exists with all required columns
- FastAPI backend with SQLModel ORM configured
- AI agent understands Model Context Protocol
- MCP communicates via HTTP with JSON
- Users authenticated before AI interaction
- All data in single PostgreSQL database
- English language only
- UTF-8 text encoding
- Synchronous tool execution
- Atomic operations
- Rate limiting infrastructure exists
- Standardized error response format available

## Dependencies *(optional)*

### External Dependencies

- Phase II completion (FastAPI + SQLModel + PostgreSQL)
- Better Auth JWT token generation/validation
- Database schema (tasks and users tables)
- MCP protocol Python library
- FastAPI framework
- Neon PostgreSQL database

### Internal Dependencies

- SQLModel Task model with required fields
- Database connection pooling
- JWT authentication middleware
- Pydantic models for validation
- Standardized error response format

### Sequencing Constraints

1. Database schema (Feature 001) must be complete first
2. Can run in parallel with AI chatbot UI
3. AI assistant cannot use tools until MCP server deployed
4. Integration tests require working JWT tokens

## Technical Constraints *(optional)*

- 5-second response timeout (target < 100ms at p95)
- Stateless architecture
- JSON-serializable data only
- UTF-8 text only
- Single database transaction per tool call
- Read-after-write consistency required
- Cannot modify tasks table structure
- Must accept Better Auth JWT tokens
- HTTP/1.1 protocol
- No client-side state management

---

## MCP Tool Specifications

### Tool Catalog

| Tool Name     | Purpose                      | Modifies Data | Auth Required |
|---------------|------------------------------|---------------|---------------|
| add_task      | Create new task              | Yes           | Yes           |
| list_tasks    | Retrieve user tasks          | No            | Yes           |
| complete_task | Toggle task completion       | Yes           | Yes           |
| delete_task   | Remove task                  | Yes           | Yes           |
| update_task   | Modify task details          | Yes           | Yes           |

### Tool: add_task

**Parameters:**
- `user_id` (string, required) - User UUID
- `title` (string, required, 1-200 chars) - Task title
- `description` (string, optional, max 1000 chars) - Task description

**Returns:** Complete task object with task_id, timestamps

**Example:**
```json
// Input
{"user_id": "550e8400-e29b-41d4-a716-446655440000", "title": "Buy groceries"}

// Output
{"task_id": "660e8400-...", "title": "Buy groceries", "completed": false, "created_at": "2025-12-27T14:30:00Z"}
```

### Tool: list_tasks

**Parameters:**
- `user_id` (string, required)
- `filter` (enum: "all"|"pending"|"completed", optional, default="all")
- `sort_by` (enum: "created_at"|"updated_at"|"title", optional)
- `sort_order` (enum: "asc"|"desc", optional)

**Returns:** Array of tasks, count, filter_applied

### Tool: complete_task

**Parameters:**
- `user_id` (string, required)
- `task_id` (string, required)

**Returns:** Updated task object with toggled completion

### Tool: delete_task

**Parameters:**
- `user_id` (string, required)
- `task_id` (string, required)

**Returns:** Deletion confirmation with task_id, deleted=true, deleted_at

### Tool: update_task

**Parameters:**
- `user_id` (string, required)
- `task_id` (string, required)
- `title` (string, optional, 1-200 chars)
- `description` (string|null, optional, max 1000 chars)

**Returns:** Updated task object

### Error Response Format

```json
{
  "error": {
    "code": "ValidationError",
    "message": "Title cannot be empty",
    "tool": "add_task"
  },
  "timestamp": "2025-12-27T15:00:00Z"
}
```

**Error Codes:** ValidationError (400), AuthorizationError (403), NotFoundError (404), DatabaseError (500)

---

*For complete tool specifications with validation rules, security notes, idempotency behavior, and detailed examples, refer to the MCP tool architecture document generated by the mcp-builder agent.*
