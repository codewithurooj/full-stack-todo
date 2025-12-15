/**
 * Tasks Page
 * Main task management interface
 * Based on specs/ui/task-management-ui.md
 */

"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { useBackendSession } from "@/lib/use-backend-session"
import { useTasks } from "@/hooks/use-tasks"
import { Navbar } from "@/components/navbar"
import { Button } from "@/components/ui/button"
import { Alert } from "@/components/ui/alert"
import { Modal } from "@/components/ui/modal"
import { TaskList } from "@/components/tasks/task-list"
import { TaskFilters, TaskFilter } from "@/components/tasks/task-filters"
import { CreateTaskForm } from "@/components/tasks/create-task-form"
import { EditTaskForm } from "@/components/tasks/edit-task-form"
import { DeleteTaskConfirmation } from "@/components/tasks/delete-task-confirmation"
import { Task } from "@/types/task"
import { PlusCircle } from "lucide-react"

export default function TasksPage() {
  const router = useRouter()
  const { data: session, isPending } = useBackendSession()
  const { tasks, isLoading, error, createTask, updateTask, deleteTask, toggleComplete } = useTasks()

  const [filter, setFilter] = React.useState<TaskFilter>("all")
  const [showCreateModal, setShowCreateModal] = React.useState(false)
  const [editingTask, setEditingTask] = React.useState<Task | null>(null)
  const [deletingTask, setDeletingTask] = React.useState<Task | null>(null)
  const [actionError, setActionError] = React.useState("")

  // Filter tasks - MUST be before conditional returns to follow Rules of Hooks
  const filteredTasks = React.useMemo(() => {
    if (!tasks) return []
    switch (filter) {
      case "active":
        return tasks.filter((task) => !task.completed)
      case "completed":
        return tasks.filter((task) => task.completed)
      default:
        return tasks
    }
  }, [tasks, filter])

  // Task counts - MUST be before conditional returns to follow Rules of Hooks
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

  // Loading state - now comes AFTER all hooks
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
                  {/* Shimmer effect */}
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

  const handleCreateTask = async (data: { title: string; description?: string }) => {
    try {
      setActionError("")
      await createTask(data)
      setShowCreateModal(false)
    } catch (err: any) {
      setActionError(err.message)
      throw err
    }
  }

  const handleUpdateTask = async (taskId: number, updates: { title?: string; description?: string }) => {
    try {
      setActionError("")
      await updateTask(taskId, updates)
      setEditingTask(null)
    } catch (err: any) {
      setActionError(err.message)
      throw err
    }
  }

  const handleDeleteTask = async (taskId: number) => {
    try {
      setActionError("")
      await deleteTask(taskId)
      setDeletingTask(null)
    } catch (err: any) {
      setActionError(err.message)
      throw err
    }
  }

  const handleToggleComplete = async (taskId: number) => {
    try {
      setActionError("")
      await toggleComplete(taskId)
    } catch (err: any) {
      setActionError(err.message)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-purple-50/20 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 right-20 w-72 h-72 bg-blue-400/5 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 left-20 w-72 h-72 bg-purple-400/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <Navbar />

      <div className="container mx-auto px-3 sm:px-4 py-4 sm:py-8 relative">
        <div className="max-w-4xl mx-auto">
          {/* Page Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 sm:mb-8">
            <div>
              <h1 className="text-2xl sm:text-3xl md:text-4xl font-extrabold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent mb-1 sm:mb-2">
                My Tasks
              </h1>
              <p className="text-gray-600 text-xs sm:text-sm">Organize and track your daily tasks</p>
            </div>
            <Button
              onClick={() => setShowCreateModal(true)}
              icon={<PlusCircle className="h-5 w-5" />}
              className="shadow-lg shadow-blue-500/30 w-full sm:w-auto"
            >
              <span className="sm:inline">New Task</span>
              <span className="hidden sm:inline"></span>
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

          {/* Filters */}
          <TaskFilters
            activeFilter={filter}
            onFilterChange={setFilter}
            taskCounts={taskCounts}
          />

          {/* Task List */}
          <TaskList
            tasks={filteredTasks}
            filter={filter}
            onTaskComplete={handleToggleComplete}
            onTaskEdit={setEditingTask}
            onTaskDelete={(taskId) => {
              const task = tasks.find((t) => t.id === taskId)
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
          onSubmit={handleCreateTask}
          onCancel={() => setShowCreateModal(false)}
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
            task={editingTask}
            onSubmit={handleUpdateTask}
            onCancel={() => setEditingTask(null)}
            onDelete={() => {
              setDeletingTask(editingTask)
              setEditingTask(null)
            }}
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
    </div>
  )
}
