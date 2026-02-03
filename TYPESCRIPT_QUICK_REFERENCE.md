# TypeScript/React Quick Reference Card

**One-page reference for common TypeScript errors and fixes**

---

## Type Errors - Quick Fixes

### ❌ Type 'X' is not assignable to type 'Y'
**Cause**: Type mismatch between definition and usage
**Fix**: Check the source type definition and match exactly
```typescript
// Check types/task.ts for source of truth
grep -r "export interface" types/
```

### ❌ This comparison appears to be unintentional
**Cause**: Comparing union type to value not in union
**Fix**: Only compare to values that exist in the type
```typescript
// ❌ pattern !== 'none' (when 'none' not in union)
// ✅ pattern !== null (when null is in union)
// ✅ pattern (truthy check)
```

### ❌ Property 'X' does not exist on type 'Y'
**Cause**: Using camelCase instead of snake_case (or vice versa)
**Fix**: Match backend field names exactly
```typescript
// ❌ filters.dateFrom
// ✅ filters.date_from
```

### ❌ Type 'Promise<void>' is not assignable to 'Promise<{ id: number }>'
**Cause**: Missing return statement in async function
**Fix**: Return the expected type
```typescript
// ✅ return { id: newTask.id }
```

### ❌ Type '() => void' is not assignable to '() => Promise<void>'
**Cause**: Forgot async keyword
**Fix**: Add async
```typescript
// ✅ onSave={async () => { ... }}
```

---

## Component Props - Valid Values

### Button Component
```typescript
size: "small" | "medium" | "large"
variant: "primary" | "secondary" | "danger" | "ghost" | "link"

// ❌ size="sm"
// ❌ variant="destructive"
```

### Filter Status
```typescript
status: "all" | "pending" | "completed"

// ❌ "active"
```

---

## JSX Structure

### Multiple Root Elements
```tsx
// ❌ Error
return (
  <div>First</div>
  <div>Second</div>
)

// ✅ Correct
return (
  <>
    <div>First</div>
    <div>Second</div>
  </>
)
```

---

## Common Missing Components

Before importing, check these UI components exist:
- `components/ui/separator.tsx`
- `components/ui/label.tsx`
- `components/ui/radio-group.tsx`
- `components/ui/select.tsx`
- `components/ui/switch.tsx`

---

## Debugging Commands

```bash
# Type check only
npm run type-check

# Find type definition
grep -r "export type RecurringPattern" frontend/

# Find all usages
grep -r "variant=" frontend/components/

# Build and check
npm run build 2>&1 | grep "Error:"

# Restart TS server (VS Code)
Cmd/Ctrl + Shift + P → "TypeScript: Restart TS Server"
```

---

## The Golden Rules

1. ✅ Check type definitions before guessing
2. ✅ Use snake_case for API field names
3. ✅ Define types once in `types/` directory
4. ✅ Read TypeScript errors carefully
5. ✅ Check UI component exists before importing
6. ✅ Wrap multiple JSX elements in `<>...</>`
7. ✅ Match Promise return types exactly
8. ✅ Use `async` for Promise-returning functions
9. ✅ Only compare values that exist in union types
10. ✅ Press F12 (Go to Definition) when unsure

---

**Last Updated**: January 12, 2026
**Full Guide**: `TYPESCRIPT_REACT_BEST_PRACTICES.md`
