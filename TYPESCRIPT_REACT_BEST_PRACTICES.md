# TypeScript & React Best Practices - Dos and Don'ts

**Purpose**: Prevent common TypeScript and React errors based on real issues encountered during Phase 5 implementation.

**Last Updated**: 2026-01-12

---

## Table of Contents
1. [Type Consistency](#type-consistency)
2. [Component Props & Variants](#component-props--variants)
3. [JSX Structure](#jsx-structure)
4. [Promise Return Types](#promise-return-types)
5. [API Naming Conventions](#api-naming-conventions)
6. [UI Component Dependencies](#ui-component-dependencies)
7. [Quick Reference Checklist](#quick-reference-checklist)

---

## Type Consistency

### Filter Status Values

❌ **DON'T**: Mix filter status values across components
```typescript
// task-list.tsx
filter?: "all" | "active" | "completed"

// types/task.ts
status?: 'all' | 'pending' | 'completed'
```

✅ **DO**: Use consistent status values across all files
```typescript
// types/task.ts - SINGLE SOURCE OF TRUTH
export interface TaskFilters {
  status?: 'all' | 'pending' | 'completed'
}

// task-list.tsx
filter?: "all" | "pending" | "completed"

// task-empty-state.tsx
filter?: "all" | "pending" | "completed"
```

**Rule**: Always reference the type definition from `types/` directory. Don't redefine types inline.

---

### Union Types - Check Before Comparing

❌ **DON'T**: Compare union types to values not in the union
```typescript
export type RecurringPattern = 'daily' | 'weekly' | 'monthly' | 'custom' | null

// This comparison is invalid!
if (pattern !== 'none') {  // ❌ 'none' is not in RecurringPattern
  // ...
}
```

✅ **DO**: Only compare to values that exist in the union type
```typescript
export type RecurringPattern = 'daily' | 'weekly' | 'monthly' | 'custom' | null

// Correct comparison
if (pattern !== null) {  // ✅ null is in the union
  // ...
}

// Or just truthy check
if (pattern) {  // ✅ Works for null check
  // ...
}
```

**Rule**: TypeScript will catch this at compile time. Read the error message carefully - it shows exactly which types don't overlap.

---

### API Property Naming - Snake Case vs Camel Case

❌ **DON'T**: Mix naming conventions
```typescript
// types/task.ts uses snake_case
export interface TaskFilters {
  date_from?: string
  date_to?: string
}

// But API client uses camelCase
if (filters.dateFrom) params.append('date_from', filters.dateFrom)  // ❌
if (filters.dateTo) params.append('date_to', filters.dateTo)  // ❌
```

✅ **DO**: Match the interface exactly
```typescript
// types/task.ts
export interface TaskFilters {
  date_from?: string
  date_to?: string
}

// API client matches interface
if (filters.date_from) params.append('date_from', filters.date_from)  // ✅
if (filters.date_to) params.append('date_to', filters.date_to)  // ✅
```

**Rule**: Backend uses snake_case, so frontend types should match. Don't transform to camelCase in TypeScript interfaces.

---

## Component Props & Variants

### Button Size Variants

❌ **DON'T**: Use non-existent size variants
```typescript
<Button size="sm" />  // ❌ 'sm' doesn't exist
<Button size="xs" />  // ❌ 'xs' doesn't exist
```

✅ **DO**: Check component definition and use valid sizes
```typescript
// button.tsx
type ButtonSize = "small" | "medium" | "large" | null | undefined

// Usage
<Button size="small" />   // ✅
<Button size="medium" />  // ✅
<Button size="large" />   // ✅
```

**Rule**: Always check the component's type definition. Don't guess prop values.

---

### Button Variant Names

❌ **DON'T**: Use variant names from other libraries
```typescript
<Button variant="destructive" />  // ❌ shadcn/ui variant, not ours
<Button variant="outline" />      // ❌ Not in our Button
```

✅ **DO**: Use defined variants from your Button component
```typescript
// button.tsx
type ButtonVariant = "primary" | "secondary" | "danger" | "ghost" | "link" | null | undefined

// Usage
<Button variant="danger" />     // ✅ For destructive actions
<Button variant="secondary" />  // ✅ For secondary actions
<Button variant="ghost" />      // ✅ For subtle actions
```

**Rule**: Check `components/ui/button.tsx` for valid variant values. We're not using shadcn/ui naming.

---

## JSX Structure

### Fragment Wrappers for Multiple Root Elements

❌ **DON'T**: Return multiple root elements without a wrapper
```typescript
if (variant === "card") {
  return (
    <div className="card">
      {/* Card content */}
    </div>
    {userId && (
      <ReminderManager />  // ❌ Second root element causes syntax error
    )}
  )
}
```

✅ **DO**: Wrap multiple root elements in a Fragment
```typescript
if (variant === "card") {
  return (
    <>
      <div className="card">
        {/* Card content */}
      </div>
      {userId && (
        <ReminderManager />  // ✅ Wrapped in Fragment
      )}
    </>
  )
}
```

**Rule**: React components must return a single root element. Use `<>...</>` (Fragment) when you need multiple.

---

### Conditional Rendering with Multiple Conditions

❌ **DON'T**: Chain conditions that can't both be true
```typescript
{showPreview && pattern && pattern !== 'none' && (
  // If pattern can only be 'daily' | 'weekly' | 'monthly' | 'custom' | null,
  // then "pattern !== 'none'" is always true (TypeScript error)
)}
```

✅ **DO**: Only check conditions that are type-safe
```typescript
{showPreview && pattern && (
  // If pattern is truthy, it's not null
  // No need for additional type-unsafe checks
)}
```

**Rule**: Let TypeScript guide you. If a comparison causes a type error, it's probably unnecessary.

---

## Promise Return Types

### Form Submit Handlers

❌ **DON'T**: Return void when ID is needed
```typescript
interface CreateTaskFormProps {
  onSubmit: (taskData: TaskCreate) => Promise<{ id: number }>
}

// Handler doesn't return the ID
const handleCreateTask = async (data: TaskCreate) => {
  const newTask = await taskApi.create(userId!, data)
  mutate()
  setShowCreateModal(false)
  // ❌ No return statement - returns Promise<void>
}
```

✅ **DO**: Return the expected type
```typescript
const handleCreateTask = async (data: TaskCreate) => {
  const newTask = await taskApi.create(userId!, data)
  mutate()
  setShowCreateModal(false)
  return { id: newTask.id }  // ✅ Returns Promise<{ id: number }>
}
```

**Rule**: Match the interface exactly. If the interface specifies a return type, always return it.

---

### Async Callback Props

❌ **DON'T**: Use sync function when async is expected
```typescript
interface RecurrenceEditorProps {
  onSave?: (pattern: RecurringPattern, ...) => Promise<void>
}

// ❌ Not async - returns void, not Promise<void>
<RecurrenceEditor
  onSave={() => {
    onRecurringChange?.()
  }}
/>
```

✅ **DO**: Mark callback as async
```typescript
// ✅ Async function returns Promise<void>
<RecurrenceEditor
  onSave={async () => {
    onRecurringChange?.()
  }}
/>
```

**Rule**: When the prop type is `Promise<T>`, the function must be `async` or explicitly return a Promise.

---

## API Naming Conventions

### Backend Field Names

❌ **DON'T**: Convert snake_case to camelCase in types
```typescript
// Backend sends: { date_from: "...", date_to: "..." }

// ❌ Wrong - doesn't match backend
export interface TaskFilters {
  dateFrom?: string
  dateTo?: string
}
```

✅ **DO**: Keep snake_case to match backend
```typescript
// Backend sends: { date_from: "...", date_to: "..." }

// ✅ Correct - matches backend exactly
export interface TaskFilters {
  date_from?: string
  date_to?: string
}
```

**Rule**: TypeScript interfaces for API data should match the backend field names exactly (usually snake_case).

---

## UI Component Dependencies

### Always Check Dependencies Before Using

❌ **DON'T**: Assume UI components exist
```typescript
import { Separator } from "@/components/ui/separator"
import { Label } from "@/components/ui/label"
import { RadioGroup } from "@/components/ui/radio-group"

// ❌ These files don't exist yet!
```

✅ **DO**: Create missing components or check they exist first
```bash
# Check if component exists
ls components/ui/separator.tsx

# If missing, create it before using
```

**Common Missing Components**:
- `separator.tsx` - Horizontal/vertical dividers
- `label.tsx` - Form labels
- `radio-group.tsx` - Radio button groups
- `switch.tsx` - Toggle switches
- `select.tsx` - Dropdown selects

**Rule**: If you're copying code from shadcn/ui examples, you might need to create the component first.

---

## Quick Reference Checklist

### Before Committing New Components

- [ ] All imports resolve (no missing UI components)
- [ ] All prop types match component definitions
- [ ] No union type comparison errors
- [ ] All async functions return Promises
- [ ] API field names match backend (snake_case)
- [ ] Filter/status values consistent across files
- [ ] Multiple root elements wrapped in Fragments
- [ ] No hardcoded values not in type unions

---

### Type Error Debugging Process

1. **Read the full error message** - TypeScript tells you exactly what's wrong
   ```
   Type '"pending"' is not assignable to type '"all" | "completed" | "active"'
   ```
   → The type definition has `"active"` but you're using `"pending"`

2. **Find the source of truth** - Check `types/` directory for canonical types
   ```typescript
   // types/task.ts is the source of truth
   export interface TaskFilters {
     status?: 'all' | 'pending' | 'completed'
   }
   ```

3. **Update all usages** - Search project-wide for the type name
   ```bash
   grep -r "status.*active" frontend/
   ```

4. **Verify imports** - Make sure UI components exist
   ```typescript
   // If this fails, create the component
   import { Separator } from "@/components/ui/separator"
   ```

---

### Common TypeScript Patterns

#### Optional Chaining for Callbacks
```typescript
// ✅ Safe - won't error if undefined
onRecurringChange?.()

// ❌ Unsafe - errors if undefined
onRecurringChange()
```

#### Truthy Checks vs Explicit Null Checks
```typescript
// ✅ Good for null/undefined check
if (pattern) {
  // pattern is not null or undefined
}

// ⚠️ Only needed if you want to distinguish null from undefined
if (pattern !== null) {
  // pattern might still be undefined
}
```

#### Fragment Shorthand
```typescript
// ✅ Preferred - cleaner
<>
  <div>First</div>
  <div>Second</div>
</>

// ✅ Also valid - more explicit
<React.Fragment>
  <div>First</div>
  <div>Second</div>
</React.Fragment>
```

---

## Real-World Examples from Phase 5

### Example 1: Type Mismatch - Filter Status

**Error**:
```
Type '"pending"' is not assignable to type '"all" | "completed" | "active"'
```

**Root Cause**: `task-list.tsx` defined `filter?: "all" | "active" | "completed"` but `types/task.ts` had `status?: 'all' | 'pending' | 'completed'`

**Fix**: Changed all instances of `"active"` to `"pending"` to match the type definition.

**Files Changed**:
- `task-list.tsx` line 22
- `task-empty-state.tsx` lines 12, 22, 26

---

### Example 2: Invalid Union Type Comparison

**Error**:
```
This comparison appears to be unintentional because the types '"daily" | "weekly" | "monthly" | "custom"' and '"none"' have no overlap.
```

**Root Cause**: RecurringPattern type is `'daily' | 'weekly' | 'monthly' | 'custom' | null`, but code checked `pattern !== 'none'`

**Fix**: Removed `pattern !== 'none'` checks, used `pattern !== null` or just `pattern` instead.

**Files Changed**:
- `recurrence-editor.tsx` lines 98, 167
- `recurring-task-form.tsx` line 184
- `useRecurring.ts` line 193

---

### Example 3: Wrong Button Variant

**Error**:
```
Type '"destructive"' is not assignable to type '"link" | "primary" | "secondary" | "danger" | "ghost"'
```

**Root Cause**: Used `variant="destructive"` (shadcn/ui naming) instead of `variant="danger"` (our naming)

**Fix**: Changed to `variant="danger"`

**File Changed**: `recurrence-editor.tsx` line 218

---

### Example 4: Missing UI Component

**Error**:
```
Module not found: Can't resolve '@/components/ui/separator'
```

**Root Cause**: Component used in code but file doesn't exist

**Fix**: Created the missing component files
- `components/ui/separator.tsx`
- `components/ui/label.tsx`
- `components/ui/radio-group.tsx`

---

### Example 5: Promise Return Type Mismatch

**Error**:
```
Type 'Promise<void>' is not assignable to type 'Promise<{ id: number }>'
```

**Root Cause**: `handleCreateTask` didn't return the task ID needed by `CreateTaskForm`

**Fix**: Added `return { id: newTask.id }` at the end of the function

**File Changed**: `app/tasks/page.tsx` line 185

---

### Example 6: JSX Syntax Error

**Error**:
```
Expected ',', got '{'
```

**Root Cause**: Multiple root elements without a Fragment wrapper

**Fix**: Wrapped the return in `<>...</>` (Fragment)

**File Changed**: `task-item.tsx` lines 65, 171

---

## Prevention Strategies

### 1. Enable TypeScript Strict Mode
```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}
```

### 2. Use ESLint with TypeScript Rules
```json
// .eslintrc.json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/recommended"
  ]
}
```

### 3. Run Type Check Before Build
```bash
# Add to package.json scripts
"type-check": "tsc --noEmit",
"prebuild": "npm run type-check"
```

### 4. Use IDE TypeScript Integration
- VS Code: Enable TypeScript IntelliSense
- Enable "TypeScript: Suggest" in settings
- Use "Go to Definition" (F12) to check types
- Use "Find All References" to check usage

---

## TypeScript Debugging Commands

### Check Types in Terminal
```bash
# Type check without building
npm run type-check

# Type check with watch mode
tsc --noEmit --watch
```

### Search for Type Definitions
```bash
# Find where a type is defined
grep -r "export type RecurringPattern" frontend/

# Find all usages of a prop
grep -r "variant=" frontend/components/

# Find all imports of a component
grep -r "from.*separator" frontend/
```

### Build and Check Errors
```bash
# Full build (includes type checking)
npm run build

# Build and show only errors (not warnings)
npm run build 2>&1 | grep "Error:"
```

---

## When TypeScript Errors Seem Wrong

Sometimes TypeScript errors can be confusing. Here's how to debug:

### 1. Check Your Imports
```typescript
// ❌ Wrong path
import { Button } from "@/components/button"

// ✅ Correct path
import { Button } from "@/components/ui/button"
```

### 2. Check for Circular Dependencies
```typescript
// If A imports B and B imports A, you get weird errors
// Solution: Extract shared types to a separate file
```

### 3. Restart TypeScript Server
```
VS Code: Cmd/Ctrl + Shift + P → "TypeScript: Restart TS Server"
```

### 4. Clear Next.js Cache
```bash
rm -rf .next
npm run build
```

---

## Summary: The Golden Rules

1. **Always check the type definition** - Don't guess prop values
2. **Match backend naming** - Use snake_case for API interfaces
3. **One source of truth** - Define types once in `types/` directory
4. **Read TypeScript errors carefully** - They tell you exactly what's wrong
5. **Check dependencies exist** - Don't assume UI components are there
6. **Wrap multiple JSX elements** - Use Fragments `<>...</>`
7. **Return what's promised** - Match Promise return types exactly
8. **Use async for Promises** - Don't forget the `async` keyword
9. **Only compare valid values** - TypeScript catches impossible comparisons
10. **When in doubt, check the component** - Go to definition (F12) to see types

---

**Last Updated**: January 12, 2026
**Based On**: Real errors from Phase 5 (Recurring Tasks) implementation
**Files Fixed**: 11 files, 16+ TypeScript errors resolved

---

## See Also

- `TIMEZONE_AND_TESTING_GUIDE.md` - Backend testing best practices
- `TIMEZONE_CHEATSHEET.md` - Quick timezone reference
- `T095_FORM_INTEGRATION_COMPLETE.md` - Detailed error resolution log
