/**
 * Task Management Hooks
 * React hooks for task CRUD operations
 */

"use client"

import useSWR from "swr"
import { Task, TaskCreate, TaskUpdate } from "@/types/task"
import { taskApi } from "@/lib/api/client"
import { useBackendSession } from "@/lib/use-backend-session"

export function useTasks() {
  const { data: session } = useBackendSession()
  const userId = session?.user?.id

  const {
    data: tasks,
    error,
    isLoading,
    mutate,
  } = useSWR<Task[]>(
    userId ? `/api/${userId}/tasks` : null,
    () => (userId ? taskApi.list(userId) : Promise.resolve([]))
  )

  const createTask = async (data: TaskCreate) => {
    if (!userId) throw new Error("User not authenticated")

    const newTask = await taskApi.create(userId, data)

    // Optimistic update
    mutate((currentTasks) => [newTask, ...(currentTasks || [])], false)

    return newTask
  }

  const updateTask = async (taskId: number, data: TaskUpdate) => {
    if (!userId) throw new Error("User not authenticated")

    const updatedTask = await taskApi.update(userId, taskId, data)

    // Optimistic update
    mutate(
      (currentTasks) =>
        currentTasks?.map((task) =>
          task.id === taskId ? updatedTask : task
        ),
      false
    )

    return updatedTask
  }

  const deleteTask = async (taskId: number) => {
    if (!userId) throw new Error("User not authenticated")

    await taskApi.delete(userId, taskId)

    // Optimistic update
    mutate(
      (currentTasks) => currentTasks?.filter((task) => task.id !== taskId),
      false
    )
  }

  const toggleComplete = async (taskId: number) => {
    if (!userId) throw new Error("User not authenticated")

    const updatedTask = await taskApi.toggleComplete(userId, taskId)

    // Optimistic update
    mutate(
      (currentTasks) =>
        currentTasks?.map((task) =>
          task.id === taskId ? updatedTask : task
        ),
      false
    )

    return updatedTask
  }

  return {
    tasks: tasks || [],
    isLoading,
    error,
    createTask,
    updateTask,
    deleteTask,
    toggleComplete,
    refresh: mutate,
  }
}
