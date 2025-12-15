# UI Specification: Task Management Interface

**Feature**: Task Management UI Components
**Created**: 2025-12-12
**Status**: Draft
**Related Specs**:
- [Task CRUD Specification](../features/001-task-crud/spec.md)
- [Shared UI Components](./shared-ui.md)

---

## Pages

### 1. Tasks Page (Main Dashboard)

**Route**: `/tasks` or `/` (home page for authenticated users)

**Layout**: Full-width application layout using AppLayout component

**Page Structure**:
```
┌─────────────────────────────────────────────────────┐
│                    Header                           │
├─────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────┐   │
│  │  Page Title: "My Tasks"    [+ New Task]     │   │
│  ├─────────────────────────────────────────────┤   │
│  │  Filter Bar: [All] [Active] [Completed]     │   │
│  ├─────────────────────────────────────────────┤   │
│  │                                              │   │
│  │          Task List                           │   │
│  │          ┌────────────────────────┐          │   │
│  │          │  Task Item 1           │          │   │
│  │          ├────────────────────────┤          │   │
│  │          │  Task Item 2           │          │   │
│  │          ├────────────────────────┤          │   │
│  │          │  Task Item 3           │          │   │
│  │          └────────────────────────┘          │   │
│  │                                              │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

**Page States**:
1. **Loading**: Shows loading spinner while fetching tasks
2. **Empty State**: No tasks exist, shows EmptyState component
3. **With Tasks**: Displays task list with filter options
4. **Creating Task**: Modal/inline form visible for new task
5. **Editing Task**: Modal/inline form visible for existing task
6. **Error State**: Shows error alert if loading fails

---

## Core Components

### 1. TaskList Component

**Purpose**: Container component that displays all tasks with filtering and organization.

**Props**:
```typescript
interface TaskListProps {
  tasks: Task[];
  onTaskClick?: (task: Task) => void;
  onTaskComplete?: (taskId: string) => void;
  onTaskEdit?: (task: Task) => void;
  onTaskDelete?: (taskId: string) => void;
  loading?: boolean;
  emptyMessage?: string;
}
```

**Visual Structure**:
- List container with proper spacing between items
- Each task rendered using TaskItem component
- Responsive grid/list layout
- Smooth transitions when tasks are added/removed
- Loading state overlay when `loading` prop is true

**Component States**:
1. **Loading**: Shows skeleton loaders or spinner
2. **Empty**: Displays EmptyState when no tasks
3. **Populated**: Shows list of TaskItem components
4. **Error**: Displays error message if provided

**Acceptance Criteria**:
1. **Given** I have 10 tasks, **When** the page loads, **Then** all 10 tasks are displayed in a vertical list
2. **Given** I am viewing my tasks, **When** I click on a task, **Then** the `onTaskClick` handler is called with the task data
3. **Given** the list is loading, **When** tasks are being fetched, **Then** I see loading indicators instead of empty content
4. **Given** I have no tasks, **When** the list renders, **Then** I see a helpful empty state message with a call-to-action

---

### 2. TaskItem Component

**Purpose**: Individual task row/card displaying task information and action buttons.

**Props**:
```typescript
interface TaskItemProps {
  task: Task;
  onComplete?: (taskId: string) => void;
  onEdit?: () => void;
  onDelete?: () => void;
  variant?: 'list' | 'card';
  showActions?: boolean;
}

interface Task {
  id: string;
  title: string;
  description?: string;
  completed: boolean;
  createdAt: string;
  updatedAt?: string;
}
```

**Visual Elements**:

**List Variant** (Default):
```
┌────────────────────────────────────────────────────┐
│ [ ] Task Title                     [Edit] [Delete] │
│     Optional description text...                   │
│     Created: 2 hours ago                           │
└────────────────────────────────────────────────────┘
```

**Card Variant**:
```
┌──────────────────────────────┐
│ [ ] Task Title               │
│                              │
│ Optional description text... │
│                              │
│ Created: 2 hours ago         │
│                              │
│ [Edit]           [Delete]    │
└──────────────────────────────┘
```

**Visual States**:
1. **Active/Incomplete** (default):
   - Unchecked checkbox
   - Normal text color
   - Full opacity
   - White/light background

2. **Completed**:
   - Checked checkbox
   - Strikethrough text on title
   - Reduced opacity (60-70%)
   - Subtle background tint (gray-50)

3. **Hover**:
   - Light background highlight
   - Show action buttons if hidden by default
   - Subtle border or shadow

4. **Focus** (keyboard navigation):
   - Clear focus ring
   - Visible to keyboard users

**Interaction Behaviors**:
- **Checkbox Click**: Toggles completion status, calls `onComplete`
- **Edit Button**: Opens edit modal/form, calls `onEdit`
- **Delete Button**: Shows confirmation, calls `onDelete`
- **Task Body Click**: Optionally expands details or opens in modal

**Acceptance Criteria**:
1. **Given** a task is incomplete, **When** I click the checkbox, **Then** the task is marked complete with strikethrough styling
2. **Given** a task is completed, **When** I click the checkbox again, **Then** the task is marked incomplete with normal styling
3. **Given** I hover over a task, **When** my cursor is over the item, **Then** I see edit and delete buttons clearly
4. **Given** a task has no description, **When** it renders, **Then** no empty space is shown for description
5. **Given** I use keyboard navigation, **When** I tab to a task, **Then** I see a clear focus indicator
6. **Given** a task was created recently, **When** it displays, **Then** I see a relative timestamp like "2 minutes ago"

---

### 3. CreateTaskForm Component

**Purpose**: Form for creating new tasks with title and optional description.

**Props**:
```typescript
interface CreateTaskFormProps {
  onSubmit: (taskData: CreateTaskData) => Promise<void>;
  onCancel?: () => void;
  initialTitle?: string;
  mode?: 'inline' | 'modal';
}

interface CreateTaskData {
  title: string;
  description?: string;
}
```

**Visual Layout**:
```
┌──────────────────────────────────────┐
│  Create New Task                     │
│                                      │
│  Title *                             │
│  [_____________________________]     │
│                                      │
│  Description (Optional)              │
│  [_____________________________]     │
│  [_____________________________]     │
│  [_____________________________]     │
│                                      │
│  [Cancel]              [Create Task] │
└──────────────────────────────────────┘
```

**Form Fields**:

1. **Title Input**:
   - Type: Single-line text input
   - Required: Yes
   - Placeholder: "What needs to be done?"
   - Max length: 200 characters
   - Validation: Cannot be empty or whitespace only
   - Auto-focus: Yes (when form opens)

2. **Description Textarea**:
   - Type: Multi-line text area
   - Required: No
   - Placeholder: "Add more details... (optional)"
   - Rows: 3 (auto-expand optional)
   - Max length: 1000 characters

**Component States**:
1. **Idle**: Form ready for input, submit button enabled when title valid
2. **Validating**: Real-time validation showing field-level errors
3. **Submitting**: Form disabled, loading indicator on submit button
4. **Error**: Server error displayed, form remains editable
5. **Success**: Form cleared and closed (in modal) or reset (if inline)

**Validation Rules**:
- Title must not be empty after trimming whitespace
- Title must be at least 1 character
- Title must not exceed 200 characters
- Description must not exceed 1000 characters if provided

**Error Messages**:
- "Task title is required"
- "Title must be at least 1 character"
- "Title cannot exceed 200 characters"
- "Description cannot exceed 1000 characters"

**Acceptance Criteria**:
1. **Given** I open the create form, **When** it appears, **Then** the title field is auto-focused
2. **Given** I type a title, **When** I click "Create Task", **Then** the task is created and added to my list
3. **Given** I try to submit without a title, **When** I click "Create Task", **Then** I see "Task title is required" error
4. **Given** I am creating a task, **When** I click "Cancel", **Then** the form closes and no task is created
5. **Given** I type more than 200 characters in title, **When** I reach the limit, **Then** I cannot type more and see character count
6. **Given** the form is submitting, **When** the API call is in progress, **Then** all fields and buttons are disabled with loading state

---

### 4. EditTaskForm Component

**Purpose**: Form for editing existing task title and description.

**Props**:
```typescript
interface EditTaskFormProps {
  task: Task;
  onSubmit: (taskId: string, updates: UpdateTaskData) => Promise<void>;
  onCancel?: () => void;
  mode?: 'inline' | 'modal';
}

interface UpdateTaskData {
  title?: string;
  description?: string;
}
```

**Visual Layout**: Same as CreateTaskForm but with:
- Pre-populated fields with existing task data
- Title: "Edit Task" instead of "Create New Task"
- Submit button: "Save Changes" instead of "Create Task"
- Additional "Delete Task" button (danger variant, positioned left)

**Form Fields**:
Same as CreateTaskForm but pre-populated with:
- Title: Current task title
- Description: Current task description (empty if not set)

**Component States**:
1. **Loading**: Fetching task data (if not passed in props)
2. **Idle**: Form ready for editing with current values
3. **Modified**: User has changed values, save button highlighted
4. **Submitting**: Form disabled, loading indicator on save button
5. **Error**: Server error displayed, form remains editable
6. **Success**: Updates saved, form closed/reset

**Validation Rules**: Same as CreateTaskForm

**Acceptance Criteria**:
1. **Given** I open edit form, **When** it loads, **Then** I see the current title and description pre-filled
2. **Given** I edit the title, **When** I click "Save Changes", **Then** the task is updated with new values
3. **Given** I haven't changed anything, **When** I look at the form, **Then** the save button indicates no changes made
4. **Given** I edit and cancel, **When** I reopen the form, **Then** I see the original values (changes were not saved)
5. **Given** I clear the description, **When** I save, **Then** the task description is removed
6. **Given** I'm editing a task, **When** I click "Delete Task", **Then** I see a confirmation dialog

---

### 5. DeleteTaskConfirmation Component

**Purpose**: Confirmation dialog before permanently deleting a task.

**Props**:
```typescript
interface DeleteTaskConfirmationProps {
  task: Task;
  onConfirm: (taskId: string) => Promise<void>;
  onCancel: () => void;
  isOpen: boolean;
}
```

**Visual Layout**:
```
┌──────────────────────────────────────┐
│  ⚠️ Delete Task?                     │
│                                      │
│  Are you sure you want to delete     │
│  this task? This action cannot be    │
│  undone.                             │
│                                      │
│  Task: "Buy groceries"               │
│                                      │
│  [Cancel]              [Delete Task] │
└──────────────────────────────────────┘
```

**Modal Properties**:
- Type: Modal dialog (from shared-ui.md)
- Size: Small (400px max-width)
- Backdrop: Semi-transparent overlay
- Close on backdrop click: Yes (calls onCancel)
- Close on Escape key: Yes (calls onCancel)

**Component States**:
1. **Closed**: Modal not visible (`isOpen: false`)
2. **Open**: Modal visible, waiting for user decision
3. **Confirming**: Delete button shows loading, buttons disabled
4. **Error**: Error message displayed, modal remains open

**Acceptance Criteria**:
1. **Given** I click delete on a task, **When** the confirmation opens, **Then** I see the task title in the warning message
2. **Given** the confirmation is open, **When** I click "Cancel", **Then** the modal closes and no deletion occurs
3. **Given** the confirmation is open, **When** I press Escape, **Then** the modal closes without deleting
4. **Given** I confirm deletion, **When** I click "Delete Task", **Then** the task is removed and the modal closes
5. **Given** deletion is in progress, **When** the API call is happening, **Then** both buttons are disabled with loading state
6. **Given** deletion fails, **When** an error occurs, **Then** I see an error message and can retry or cancel

---

### 6. TaskFilters Component

**Purpose**: Filter tabs/buttons to show All, Active, or Completed tasks.

**Props**:
```typescript
interface TaskFiltersProps {
  activeFilter: TaskFilter;
  onFilterChange: (filter: TaskFilter) => void;
  taskCounts?: TaskCounts;
}

type TaskFilter = 'all' | 'active' | 'completed';

interface TaskCounts {
  all: number;
  active: number;
  completed: number;
}
```

**Visual Layout**:
```
┌──────────────────────────────────────────┐
│  [All (24)] [Active (18)] [Completed (6)]│
└──────────────────────────────────────────┘
```

**Filter Buttons**:
- **All**: Shows all tasks (active + completed)
- **Active**: Shows only incomplete tasks
- **Completed**: Shows only completed tasks

**Visual States**:
- **Active Filter**: Primary color background, white text, bold
- **Inactive Filters**: Transparent background, primary text, normal weight
- **Hover**: Light background tint on inactive filters

**Layout**:
- Horizontal flex container
- Buttons have equal spacing
- Mobile: Full-width buttons stacked or scrollable horizontal

**Acceptance Criteria**:
1. **Given** I am viewing all tasks, **When** I see the filters, **Then** the "All" filter is highlighted as active
2. **Given** I click "Active", **When** the filter changes, **Then** I see only incomplete tasks
3. **Given** I click "Completed", **When** the filter changes, **Then** I see only completed tasks with strikethrough
4. **Given** filters show counts, **When** I complete a task, **Then** the counts update immediately
5. **Given** I am on mobile, **When** I view filters, **Then** they remain easily tappable (minimum 44px touch targets)

---

### 7. EmptyState Component (Task-Specific)

**Purpose**: Friendly message and call-to-action when no tasks match current filter.

**Props**:
```typescript
interface TaskEmptyStateProps {
  filter: TaskFilter;
  onCreateTask?: () => void;
}
```

**Visual Layouts**:

**No Tasks at All**:
```
┌────────────────────────────────────┐
│                                    │
│         📝                         │
│                                    │
│    No tasks yet!                   │
│    Create your first task to       │
│    get started.                    │
│                                    │
│    [+ Create Your First Task]      │
│                                    │
└────────────────────────────────────┘
```

**No Active Tasks**:
```
┌────────────────────────────────────┐
│                                    │
│         ✅                         │
│                                    │
│    All done!                       │
│    You have no active tasks.       │
│                                    │
└────────────────────────────────────┘
```

**No Completed Tasks**:
```
┌────────────────────────────────────┐
│                                    │
│         📋                         │
│                                    │
│    No completed tasks yet          │
│    Complete a task to see it here. │
│                                    │
└────────────────────────────────────┘
```

**Visual Properties**:
- Center-aligned content
- Large icon/emoji (48-64px)
- Heading text (text-lg, font-semibold)
- Description text (text-base, text-gray-600)
- Optional CTA button (primary variant)
- Generous padding (py-12 or py-16)

**Acceptance Criteria**:
1. **Given** I have no tasks, **When** I view the tasks page, **Then** I see "No tasks yet!" with a create button
2. **Given** I filter to "Active" with no active tasks, **When** I view the list, **Then** I see "All done!" message
3. **Given** I click the CTA button, **When** it's clicked, **Then** the create task form opens
4. **Given** the empty state is displayed, **When** I see it, **Then** the message matches my current filter context

---

### 8. TaskStats Component (Optional Enhancement)

**Purpose**: Display task statistics and progress summary.

**Props**:
```typescript
interface TaskStatsProps {
  totalTasks: number;
  completedTasks: number;
  activeTasks: number;
  variant?: 'compact' | 'detailed';
}
```

**Visual Layout (Compact)**:
```
┌──────────────────────────────────────────┐
│  📊 Progress: 6 of 24 completed (25%)    │
└──────────────────────────────────────────┘
```

**Visual Layout (Detailed)**:
```
┌──────────────────────────────────────────┐
│  Task Statistics                         │
│                                          │
│  Total Tasks: 24                         │
│  Active: 18        Completed: 6          │
│                                          │
│  [████████░░░░░░░░] 25% Complete         │
└──────────────────────────────────────────┘
```

**Visual Elements**:
- Statistics numbers (font-semibold, text-lg)
- Progress bar (colored based on completion %)
- Color coding: <30% red, 30-70% yellow, >70% green

**Acceptance Criteria**:
1. **Given** I complete a task, **When** the stats update, **Then** I see the completion percentage increase
2. **Given** I have completed all tasks, **When** viewing stats, **Then** I see 100% with green color
3. **Given** I view stats, **When** calculating percentage, **Then** it shows rounded to nearest whole number

---

## Component Composition & Layouts

### Task Management Page Structure

**Component Hierarchy**:
```
AppLayout (from shared-ui)
└── TasksPage
    ├── PageHeader
    │   ├── Heading: "My Tasks"
    │   └── Button: "+ New Task"
    ├── TaskFilters
    ├── TaskStats (optional)
    └── TaskList
        ├── TaskItem (repeated)
        │   ├── Checkbox
        │   ├── TaskContent
        │   └── TaskActions
        │       ├── Button: Edit
        │       └── Button: Delete
        └── EmptyState (conditional)

Modal (from shared-ui)
├── CreateTaskForm (when creating)
└── EditTaskForm (when editing)

Modal (from shared-ui)
└── DeleteTaskConfirmation (when deleting)
```

### Responsive Behavior

**Desktop (≥1024px)**:
- Task items in single column list (max-width: 800px, centered)
- Action buttons always visible on hover
- Modal dialogs: 600px width
- Filters: Horizontal layout with all options visible

**Tablet (768px - 1023px)**:
- Task items in single column, full width with padding
- Action buttons always visible (no hover required)
- Modal dialogs: 80% viewport width
- Filters: Horizontal layout, slightly compressed

**Mobile (<768px)**:
- Task items: Full width, increased padding
- Card variant recommended over list variant
- Action buttons: Revealed via swipe gesture or always visible
- Modal dialogs: Full screen or 95% viewport width
- Filters: Full-width buttons or horizontal scroll
- Create button: Fixed floating action button (bottom-right)

---

## Styling Guidelines

### Task Item Styling

**Base Styles**:
```css
/* Pseudo-CSS for specification purposes */
.task-item {
  padding: 16px;
  border: 1px solid var(--color-gray-200);
  border-radius: 8px;
  background: white;
  transition: all 0.2s ease;
}

.task-item:hover {
  background: var(--color-gray-50);
  border-color: var(--color-gray-300);
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.task-item.completed {
  opacity: 0.6;
  background: var(--color-gray-50);
}

.task-item.completed .task-title {
  text-decoration: line-through;
  color: var(--color-gray-500);
}
```

### Form Styling

Follow shared-ui.md specifications for:
- Input components
- Button components
- Form validation states
- Error message display

### Animation & Transitions

**Task Operations**:
- Task creation: Fade in + slide down (300ms)
- Task deletion: Fade out + collapse height (200ms)
- Task completion toggle: Checkbox animation (150ms) + text strikethrough transition (200ms)
- Filter change: Cross-fade between lists (250ms)

**Form Interactions**:
- Modal open: Fade in backdrop (200ms) + scale up content (250ms)
- Modal close: Fade out backdrop (200ms) + scale down content (200ms)
- Form submission: Button loading spinner fade in (150ms)

---

## Accessibility Requirements

All components must meet WCAG AA standards (reference shared-ui.md).

### Task-Specific Accessibility

**TaskItem**:
- Checkbox: Proper label association, keyboard accessible
- Task title: Heading level appropriate to page structure (h2 or h3)
- Action buttons: Clear aria-labels ("Edit task: Buy groceries", "Delete task: Buy groceries")
- Completed state: aria-label includes "completed" status

**TaskList**:
- Semantic list markup (`<ul>` with `<li>` items)
- Keyboard navigation: Tab through tasks, Enter to select/edit
- Screen reader announcements when tasks are added/removed
- Live region for task count updates

**Forms**:
- All fields have associated labels (visible or aria-label)
- Error messages: aria-live="polite" for validation errors
- Required fields: Marked with aria-required="true" and visual indicator
- Focus management: Return focus to trigger element after modal closes

**Keyboard Shortcuts** (Optional Enhancement):
- `N` or `C`: Open create task form
- `Arrow Up/Down`: Navigate between tasks
- `Space`: Toggle task completion
- `E`: Edit focused task
- `Delete`: Delete focused task (with confirmation)
- `Escape`: Close modal/form

---

## Performance Considerations

### Rendering Optimization

**TaskList**:
- Virtualize list for >100 tasks (react-window or similar)
- Memoize TaskItem components to prevent unnecessary re-renders
- Debounce filter changes (100ms)
- Optimize task completion toggle (optimistic UI update)

**Forms**:
- Debounce validation (300ms after typing stops)
- Lazy load modal components (code splitting)
- Cache form state to prevent data loss on unmount

### Loading States

**Initial Page Load**:
1. Show skeleton loaders (3-5 task item skeletons)
2. Load task data from API
3. Fade in actual tasks, remove skeletons

**Task Operations**:
- **Create**: Optimistic UI - add task immediately, show loading state, rollback on error
- **Update**: Optimistic UI - update task immediately, show loading indicator, rollback on error
- **Delete**: Confirm first, then optimistic removal with undo option (3-second snackbar)
- **Complete Toggle**: Instant visual feedback, API call in background

---

## Error Handling

### Error Scenarios

**Network Errors**:
- Message: "Unable to connect. Please check your internet connection."
- Action: Retry button, automatic retry after 3 seconds

**Server Errors (5xx)**:
- Message: "Something went wrong on our end. Please try again in a moment."
- Action: Retry button, error logged for debugging

**Validation Errors (4xx)**:
- Message: Specific field-level error messages
- Action: Highlight invalid fields, provide correction guidance

**Not Found (404)**:
- Message: "This task no longer exists."
- Action: Remove from UI, offer to refresh list

### Error Display

- **Inline Errors**: Below form fields (validation errors)
- **Toast Notifications**: Top-right corner (operation errors)
- **Alert Banners**: Top of task list (critical errors)
- **Modal Alerts**: For blocking errors requiring acknowledgment

---

## Success Criteria

### Usability Metrics

- **SC-001**: Users can create a new task in under 10 seconds from clicking "+ New Task"
- **SC-002**: Users can toggle task completion with a single click/tap
- **SC-003**: Users can filter tasks with a single click showing results in under 500ms
- **SC-004**: Users can edit a task title and save changes in under 15 seconds
- **SC-005**: Users see immediate visual feedback (under 100ms) when interacting with any task element

### Accessibility Metrics

- **SC-006**: All interactive elements are keyboard accessible following logical tab order
- **SC-007**: Screen readers announce task status, count, and updates accurately
- **SC-008**: Color contrast ratios meet WCAG AA standards (4.5:1 for normal text)
- **SC-009**: Touch targets on mobile are minimum 44x44px for all interactive elements
- **SC-010**: Users can complete all task operations using only keyboard navigation

### Performance Metrics

- **SC-011**: Task list renders in under 300ms for up to 50 tasks
- **SC-012**: Filter changes complete in under 200ms
- **SC-013**: Task completion toggles update UI in under 100ms (optimistic)
- **SC-014**: Forms open/close with smooth animations (no jank, 60fps)
- **SC-015**: Page remains responsive during task operations (no blocking)

### Visual Consistency

- **SC-016**: All task components use colors from shared design tokens
- **SC-017**: Spacing between elements follows 4px grid system consistently
- **SC-018**: Typography uses defined font sizes and weights from shared-ui
- **SC-019**: All buttons use consistent variants and states across components
- **SC-020**: Animations follow consistent timing and easing functions

### Error Handling

- **SC-021**: Users see clear error messages for all failure scenarios
- **SC-022**: Failed operations allow users to retry without losing entered data
- **SC-023**: Network errors are distinguishable from validation errors
- **SC-024**: Users can recover from errors without refreshing the page

### Mobile Experience

- **SC-025**: All task operations are fully functional on mobile devices
- **SC-026**: Forms are usable on mobile without horizontal scrolling
- **SC-027**: Task list is scrollable and performant on mobile (60fps)
- **SC-028**: Modals display appropriately on small screens without content cutoff

---

## Integration Points

### API Integration

Components expect the following API operations (see `specs/api/rest-endpoints.md` when created):

```typescript
// Task API interface
interface TaskAPI {
  // GET /api/{user_id}/tasks
  getTasks(): Promise<Task[]>;

  // POST /api/{user_id}/tasks
  createTask(data: CreateTaskData): Promise<Task>;

  // PUT /api/{user_id}/tasks/{id}
  updateTask(id: string, data: UpdateTaskData): Promise<Task>;

  // DELETE /api/{user_id}/tasks/{id}
  deleteTask(id: string): Promise<void>;

  // PATCH /api/{user_id}/tasks/{id}/complete
  toggleTaskComplete(id: string): Promise<Task>;
}
```

### Authentication Integration

- All task operations require authenticated user session
- User ID is extracted from JWT token in authentication context
- Unauthorized requests redirect to sign-in page
- Session expiration during task operations shows re-authentication prompt

### State Management

Recommended state management approach:
- **Server State**: React Query, SWR, or similar for API data
- **UI State**: React useState/useReducer for forms, modals
- **Global State**: Context API for user session, theme (if needed)

---

## Testing Guidelines

### Component Testing

Each component should have tests for:
1. **Rendering**: Component renders with required props
2. **User Interactions**: Clicks, typing, keyboard navigation
3. **State Changes**: Component responds to prop/state changes
4. **Accessibility**: ARIA attributes, keyboard support, screen reader compatibility
5. **Edge Cases**: Empty states, error states, loading states

### Example Test Scenarios

**TaskItem Component**:
```
✓ Renders task title and description
✓ Clicking checkbox calls onComplete with task ID
✓ Clicking edit button calls onEdit handler
✓ Clicking delete button calls onDelete handler
✓ Completed tasks show strikethrough styling
✓ Hover state shows action buttons
✓ Keyboard focus shows focus ring
✓ Screen reader announces task status correctly
```

**CreateTaskForm Component**:
```
✓ Auto-focuses title input on mount
✓ Submit button disabled when title is empty
✓ Shows validation error for empty title on submit
✓ Calls onSubmit with correct data structure
✓ Shows loading state during submission
✓ Clears form after successful submission
✓ Cancel button calls onCancel handler
✓ Character count updates as user types
```

### Integration Testing

Test complete user flows:
1. **Create Task Flow**: Open form → Enter data → Submit → See task in list
2. **Complete Task Flow**: Click checkbox → See strikethrough → Filter to completed
3. **Edit Task Flow**: Click edit → Modify data → Save → See updates in list
4. **Delete Task Flow**: Click delete → Confirm → Task removed from list
5. **Filter Flow**: Click filter → See filtered tasks → Counts update

---

## Future Enhancements

Features not included in this specification but valuable for future iterations:

- **Task Categories/Tags**: Organize tasks by category or label
- **Task Priority Levels**: High, medium, low priority indicators
- **Task Due Dates**: Calendar integration and due date reminders
- **Task Search**: Search tasks by title or description
- **Task Sorting**: Sort by date, completion, priority, alphabetical
- **Bulk Operations**: Select multiple tasks for batch actions
- **Task Archiving**: Archive completed tasks instead of deleting
- **Task Notes/Comments**: Add additional notes to tasks
- **Task Attachments**: Upload files associated with tasks
- **Subtasks/Checklists**: Break down tasks into smaller items
- **Task Templates**: Create tasks from predefined templates
- **Keyboard Shortcuts**: Power-user keyboard commands
- **Drag & Drop Reordering**: Manual task order customization
- **Task Sharing**: Share tasks with other users
- **Task History**: View edit history and changes
- **Dark Mode**: Theme toggle for dark/light modes
- **Offline Support**: PWA with offline task management
- **Task Export**: Export tasks to CSV, JSON, or other formats

---

## Notes

- All TypeScript interfaces are illustrative and show structure, not implementation details
- Components should be built using React best practices (hooks, composition, etc.)
- Refer to `shared-ui.md` for base component implementations (Button, Input, Modal, etc.)
- Follow Next.js 16+ App Router conventions for routing and data fetching
- Use Better Auth session context for user authentication state
- Implement responsive design mobile-first with Tailwind CSS breakpoints
- All dates/times should be formatted according to user locale/preferences
