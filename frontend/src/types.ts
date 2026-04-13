export type ActivityKind = 'habit' | 'reminder'

export interface Activity {
  id: string
  activity_name: string
  activity_kind: ActivityKind
  status: string
  created_at: string
  completed_at: string | null
  start_at: string | null
  deadline_at: string | null
  reminder_offsets_minutes: number[] | null
}

export interface ProgressBucket {
  completed: number
  total: number
}

export interface ProgressSummary {
  period_start: string
  period_end: string
  total_planned: number
  total_completed: number
  habits: ProgressBucket
  reminders: ProgressBucket
  completion_rate: number
}

export interface ActivityCreatePayload {
  activity_name: string
  activity_kind: ActivityKind
  start_at?: string
  deadline_at: string
  reminder_offsets_minutes: number[]
}

export interface ActivityUpdatePayload {
  activity_name?: string
  start_at?: string | null
  deadline_at?: string
  reminder_offsets_minutes?: number[]
}

export interface HabitProgress {
  habit_name: string
  done: number
  missed: number
  total: number
}
