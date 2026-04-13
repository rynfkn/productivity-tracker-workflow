import type { Activity, ActivityCreatePayload, ActivityUpdatePayload, HabitProgress, ProgressSummary } from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers || {}),
    },
    ...init,
  })

  if (!response.ok) {
    let message = `Request failed: ${response.status}`
    try {
      const data = await response.json()
      message = data?.detail || data?.message || message
    } catch {
      // ignore invalid json in error response
    }
    throw new Error(message)
  }

  return response.json() as Promise<T>
}

export function listActivities() {
  return request<Activity[]>('/api/activities')
}

export function createActivity(payload: ActivityCreatePayload) {
  return request<Activity>('/api/activities', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateActivity(id: string, payload: ActivityUpdatePayload) {
  return request<Activity>(`/api/activities/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export function deleteActivity(id: string) {
  return request<void>(`/api/activities/${id}`, { method: 'DELETE' })
}

export function getTodayProgress() {
  return request<ProgressSummary>('/api/progress/today')
}

export function getHabitProgress() {
  return request<HabitProgress[]>('/api/habits/progress')
}

export function getCompletions() {
  return request<Activity[]>('/api/completions')
}
