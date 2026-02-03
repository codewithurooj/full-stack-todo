/**
 * Tasks Page - Enhanced with Intermediate Features
 * Main task management interface with search, filters, and sorting
 * Based on specs/009-intermediate-features/spec.md
 */

"use client"

import * as React from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { useBackendSession } from "@/lib/use-backend-session"
import { useToast } from "@/components/ui/toast"
import { useKeyboardShortcuts } from "@/hooks/use-keyboard-shortcuts"
import { Confetti } from "@/components/ui/confetti"
import { KeyboardShortcutsModal } from "@/components/ui/keyboard-shortcuts-modal"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Alert } from "@/components/ui/alert"
import { Modal } from "@/components/ui/modal"
import { TaskList } from "@/components/tasks/task-list"
import { SearchBar } from "@/components/tasks/search-bar"
import { AdvancedTaskFilters, AdvancedFilterValues } from "@/components/tasks/advanced-task-filters"
import { SortDropdown } from "@/components/tasks/sort-dropdown"
import { CreateTaskForm } from "@/components/tasks/create-task-form"
import { EditTaskForm } from "@/components/tasks/edit-task-form"
import { DeleteTaskConfirmation } from "@/components/tasks/delete-task-confirmation"
import { Task, TaskCreate, TaskUpdate, TaskFilters } from "@/types/task"
import { taskApi } from "@/lib/api/client"
import { PlusCircle } from "lucide-react"
import useSWR from "swr"

export default function TasksPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { data: session, isPending } = useBackendSession()
  const { showToast } = useToast()

  // URL-based filter state
  const [search, setSearch] = React.useState(searchParams.get('search') || '')
  const [sortBy, setSortBy] = React.useState(searchParams.get('sort_by') || 'created_at')
  const [sortOrder, setSortOrder] = React.useState<'asc' | 'desc'>(
    (searchParams.get('sort_order') as 'asc' | 'desc') || 'desc'
  )
  const [filters, setFilters] = React.useState<AdvancedFilterValues>({
    priority: searchParams.get('priority') as any,
    status: (searchParams.get('status') as any) || 'all',
    tags: searchParams.getAll('tags'),
    dateFrom: searchParams.get('date_from') || undefined,
    dateTo: searchParams.get('date_to') || undefined,
  })

  // Modal states
  const [showCreateModal, setShowCreateModal] = React.useState(false)
  const [editingTask, setEditingTask] = React.useState<Task | null>(null)
  const [deletingTask, setDeletingTask] = React.useState<Task | null>(null)
  const [actionError, setActionError] = React.useState("")
  const [showConfetti, setShowConfetti] = React.useState(false)
  const [showShortcuts, setShowShortcuts] = React.useState(false)

  const userId = session?.user?.id

  // Fetch tasks with filters
  const taskFilters: TaskFilters = React.useMemo(() => ({
    search: search || undefined,
    sort: sortBy as any,
    order: sortOrder,
    ...filters,
  }), [search, sortBy, sortOrder, filters])

  const { data: tasks, error, isLoading, mutate } = useSWR<Task[]>(
    userId ? [`/api/${userId}/tasks`, taskFilters] : null,
    () => userId ? taskApi.list(userId, taskFilters) : Promise.resolve([])
  )

  // Fetch available tags for autocomplete
  const { data: tagsData } = useSWR(
    userId ? `/api/${userId}/tasks/tags` : null,
    () => userId ? taskApi.getTags(userId) : Promise.resolve({ tags: [], usage_count: {} })
  )

  const availableTags = tagsData?.tags || []

  // Update URL when filters change
  React.useEffect(() => {
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (sortBy !== 'created_at') params.set('sort_by', sortBy)
    if (sortOrder !== 'desc') params.set('sort_order', sortOrder)
    if (filters.priority) params.set('priority', filters.priority)
    if (filters.status && filters.status !== 'all') params.set('status', filters.status)
    if (filters.dateFrom) params.set('date_from', filters.dateFrom)
    if (filters.dateTo) params.set('date_to', filters.dateTo)
    filters.tags?.forEach(tag => params.append('tags', tag))

    const newUrl = params.toString() ? `?${params.toString()}` : '/tasks'
    router.replace(newUrl, { scroll: false })
  }, [search, sortBy, sortOrder, filters, router])

  // Keyboard shortcuts
  useKeyboardShortcuts([
    {
      key: "n",
      description: "New task",
      action: () => setShowCreateModal(true),
    },
    {
      key: "?",
      description: "Show shortcuts",
      action: () => setShowShortcuts(true),
    },
    {
      key: "c",
      description: "Open chat",
      action: () => router.push("/chat"),
    },
    {
      key: "t",
      description: "Go to tasks",
      action: () => router.push("/tasks"),
    },
  ])

  // Filtered tasks (for local display filtering)
  const filteredTasks = React.useMemo(() => {
    if (!tasks) return []
    return tasks
  }, [tasks])

  // Task counts
  const taskCounts = React.useMemo(
    () => ({
      all: tasks?.length || 0,
      active: tasks?.filter((t) => !t.completed).length || 0,
      completed: tasks?.filter((t) => t.completed).length || 0,
    }),
    [tasks]
  )

  // Redirect to signin if not authenticated
  React.useEffect(() => {
    if (!isPending && !session?.user) {
      router.push("/auth/signin")
    }
  }, [isPending, session, router])

  // Loading state
  if (isPending || isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50/30">
        <Navbar />
        <div className="container mx-auto px-4 py-8">
          <div className="max-w-4xl mx-auto">
            <div className="h-10 w-48 bg-gradient-to-r from-gray-200 to-gray-300 animate-pulse rounded-lg mb-6" />
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="relative p-5 rounded-xl border-2 border-gray-200 bg-white overflow-hidden"
                >
                  <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/60 to-transparent" />
                  <div className="flex items-start gap-4">
                    <div className="h-5 w-5 bg-gray-200 rounded animate-pulse" />
                    <div className="flex-1 space-y-3">
                      <div className="h-5 bg-gray-200 rounded-md w-3/4 animate-pulse" />
                      <div className="h-4 bg-gray-200 rounded-md w-full animate-pulse" />
                      <div className="h-3 bg-gray-200 rounded-md w-1/4 animate-pulse" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  const handleCreateTask = async (data: TaskCreate) => {
    try {
      setActionError("")
      const newTask = await taskApi.create(userId!, data)
      mutate()
      setShowCreateModal(false)
      showToast("Task created successfully!", "success")
      return { id: newTask.id }
    } catch (err: any) {
      setActionError(err.message)
      showToast(err.message || "Failed to create task", "error")
      throw err
    }
  }

  const handleUpdateTask = async (taskId: number, updates: TaskUpdate) => {
    try {
      setActionError("")
      await taskApi.update(userId!, taskId, updates)
      mutate()
      setEditingTask(null)
      showToast("Task updated successfully!", "success")
    } catch (err: any) {
      setActionError(err.message)
      showToast(err.message || "Failed to update task", "error")
      throw err
    }
  }

  const handleDeleteTask = async (taskId: number) => {
    try {
      setActionError("")
      await taskApi.delete(userId!, taskId)
      mutate()
      setDeletingTask(null)
      showToast("Task deleted successfully!", "success")
    } catch (err: any) {
      setActionError(err.message)
      showToast(err.message || "Failed to delete task", "error")
      throw err
    }
  }

  const handleToggleComplete = async (taskId: number) => {
    try {
      setActionError("")
      const task = tasks?.find((t) => t.id === taskId)
      await taskApi.toggleComplete(userId!, taskId)
      mutate()
      if (task) {
        if (!task.completed) {
          setShowConfetti(true)
          showToast("Task completed! Great job!", "success")
        } else {
          showToast("Task marked as incomplete", "success")
        }
      }
    } catch (err: any) {
      setActionError(err.message)
      showToast(err.message || "Failed to toggle completion", "error")
    }
  }

  const handleSortChange = (newSortBy: string, newSortOrder: 'asc' | 'desc') => {
    setSortBy(newSortBy)
    setSortOrder(newSortOrder)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/20 relative overflow-hidden">
      <Confetti trigger={showConfetti} onComplete={() => setShowConfetti(false)} />

      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 right-20 w-72 h-72 bg-blue-400/5 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 left-20 w-72 h-72 bg-purple-400/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <Navbar />

      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-8 relative">
        <div className="max-w-6xl mx-auto">
          {/* Page Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 sm:mb-8">
            <div>
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent mb-1 sm:mb-2">
                My Tasks
              </h1>
              <p className="text-gray-600 text-xs sm:text-sm">
                Organize and track your daily tasks with priorities, tags, and filters
              </p>
            </div>
            <Button
              onClick={() => setShowCreateModal(true)}
              icon={<PlusCircle className="h-5 w-5" />}
              className="shadow-lg shadow-blue-500/30 w-full sm:w-auto"
            >
              <span className="sm:inline">New Task</span>
            </Button>
          </div>

          {/* Error Alert */}
          {(error || actionError) && (
            <Alert
              variant="error"
              message={error?.message || actionError}
              dismissible
              onClose={() => setActionError("")}
              className="mb-6"
            />
          )}

          {/* Search and Sort Controls */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="md:col-span-2">
              <SearchBar
                value={search}
                onChange={setSearch}
                resultCount={filteredTasks.length}
                placeholder="Search tasks by title or description..."
              />
            </div>
            <div>
              <SortDropdown
                sortBy={sortBy}
                sortOrder={sortOrder}
                onSortChange={handleSortChange}
              />
            </div>
          </div>

          {/* Advanced Filters */}
          <AdvancedTaskFilters
            filters={filters}
            onFilterChange={setFilters}
            availableTags={availableTags}
            className="mb-6"
          />

          {/* Task List */}
          <TaskList
            tasks={filteredTasks}
            filter={filters.status || 'all'}
            onTaskComplete={handleToggleComplete}
            onTaskEdit={setEditingTask}
            onTaskDelete={(taskId) => {
              const task = tasks?.find((t) => t.id === taskId)
              if (task) setDeletingTask(task)
            }}
          />
        </div>
      </div>

      {/* Create Task Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        size="medium"
      >
        <CreateTaskForm
          userId={userId}
          onSubmit={handleCreateTask}
          onCancel={() => setShowCreateModal(false)}
          availableTags={availableTags}
        />
      </Modal>

      {/* Edit Task Modal */}
      {editingTask && (
        <Modal
          isOpen={true}
          onClose={() => setEditingTask(null)}
          size="medium"
        >
          <EditTaskForm
            userId={userId}
            task={editingTask}
            onSubmit={handleUpdateTask}
            onCancel={() => setEditingTask(null)}
            onDelete={() => {
              setDeletingTask(editingTask)
              setEditingTask(null)
            }}
            availableTags={availableTags}
            onRecurringChange={mutate}
          />
        </Modal>
      )}

      {/* Delete Confirmation Modal */}
      {deletingTask && (
        <Modal
          isOpen={true}
          onClose={() => setDeletingTask(null)}
          size="small"
        >
          <DeleteTaskConfirmation
            task={deletingTask}
            onConfirm={handleDeleteTask}
            onCancel={() => setDeletingTask(null)}
          />
        </Modal>
      )}

      {/* Keyboard Shortcuts Help */}
      <KeyboardShortcutsModal
        isOpen={showShortcuts}
        onClose={() => setShowShortcuts(false)}
      />
    </div>
  )
}
