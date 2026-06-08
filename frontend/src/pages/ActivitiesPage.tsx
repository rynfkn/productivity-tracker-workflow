import { type FormEvent, useEffect, useMemo, useState } from 'react'
import DatePicker from 'react-datepicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns'
import { TimeClock } from '@mui/x-date-pickers/TimeClock'
import { CalendarClock, Check, ChevronDown, ChevronUp, Clock, RotateCcw } from 'lucide-react'
import 'react-datepicker/dist/react-datepicker.css'
import { createActivity, deleteActivity, listActivities, updateActivity, updateActivityStatus } from '../api'
import type { Activity, ActivityCreatePayload, ActivityKind, ActivityUpdatePayload } from '../types'

interface FormState {
  activity_name: string
  activity_kind: ActivityKind
  start_at: Date | null
  deadline_at: Date | null
  offsets_text: string
}

function roundToNearest(minutesStep: number, date: Date): Date {
  const copy = new Date(date)
  const ms = 1000 * 60 * minutesStep
  return new Date(Math.ceil(copy.getTime() / ms) * ms)
}

function createInitialForm(): FormState {
  const nowRounded = roundToNearest(15, new Date())
  const start = new Date(nowRounded)
  start.setMinutes(start.getMinutes() + 5)
  const deadline = new Date(nowRounded)
  deadline.setHours(deadline.getHours() + 1)
  return {
    activity_name: '',
    activity_kind: 'habit',
    start_at: start,
    deadline_at: deadline,
    offsets_text: '30',
  }
}

function formFromActivity(item: Activity): FormState {
  return {
    activity_name: item.activity_name,
    activity_kind: item.activity_kind,
    start_at: item.start_at ? new Date(item.start_at) : null,
    deadline_at: item.deadline_at ? new Date(item.deadline_at) : null,
    offsets_text: item.reminder_offsets_minutes?.join(', ') ?? '30',
  }
}

function formatDateTime(value: string | null) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

function isDone(item: Activity): boolean {
  return item.status === 'done' || Boolean(item.completed_at)
}

function isIncomplete(item: Activity): boolean {
  return !isDone(item)
}

function isPastDue(item: Activity, now: Date): boolean {
  if (!item.deadline_at || !isIncomplete(item)) return false
  return new Date(item.deadline_at).getTime() < now.getTime()
}

function toIso(date: Date): string {
  return date.toISOString()
}

function dateOrRoundedNow(value: Date | null): Date {
  return value ? new Date(value) : roundToNearest(15, new Date())
}

function withDate(current: Date | null, selectedDate: Date | null): Date | null {
  if (!selectedDate) return null
  const next = dateOrRoundedNow(current)
  next.setFullYear(selectedDate.getFullYear(), selectedDate.getMonth(), selectedDate.getDate())
  return next
}

function withClockTime(current: Date | null, clockValue: Date | null): Date | null {
  if (!clockValue) return current
  const next = dateOrRoundedNow(current)
  next.setHours(clockValue.getHours(), clockValue.getMinutes(), 0, 0)
  return next
}

function parseOffsets(input: string): number[] {
  const values = input
    .split(',')
    .map((x) => x.trim())
    .filter(Boolean)
    .map((x) => Number(x))
    .filter((x) => Number.isInteger(x) && x >= 0)
  return Array.from(new Set(values)).sort((a, b) => a - b)
}

function kindChipClass(kind: ActivityKind): string {
  return kind === 'habit'
    ? 'border-violet-200 bg-violet-100 text-violet-700 dark:border-violet-800 dark:bg-violet-900/40 dark:text-violet-300'
    : 'border-blue-200 bg-blue-100 text-blue-700 dark:border-blue-800 dark:bg-blue-900/40 dark:text-blue-300'
}

function statusChipClass(status: string): string {
  if (status === 'done')
    return 'border-emerald-200 bg-emerald-100 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
  if (status === 'failed')
    return 'border-rose-200 bg-rose-100 text-rose-700 dark:border-rose-800 dark:bg-rose-900/40 dark:text-rose-300'
  if (status === 'missed')
    return 'border-orange-200 bg-orange-100 text-orange-700 dark:border-orange-800 dark:bg-orange-900/40 dark:text-orange-300'
  return 'border-amber-200 bg-amber-100 text-amber-700 dark:border-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
}

const inputClass =
  'min-w-0 rounded-md border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition-shadow focus:border-slate-400 focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:focus:ring-slate-800 text-slate-900 dark:text-slate-100'

interface SchedulePickerProps {
  label: string
  value: Date | null
  placeholder: string
  onChange: (value: Date | null) => void
}

function SchedulePicker({ label, value, placeholder, onChange }: SchedulePickerProps) {
  const selectedTime = dateOrRoundedNow(value)

  return (
    <div className="grid gap-2">
      <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{label}</span>
      <div className="rounded-lg border border-slate-200 bg-slate-50/80 p-2.5 dark:border-slate-800 dark:bg-slate-950/50">
        <div className="flex min-w-0 items-center gap-2">
          <div className="grid h-9 w-9 shrink-0 place-items-center rounded-md bg-white text-slate-500 shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:text-slate-400 dark:ring-slate-800">
            <CalendarClock aria-hidden="true" size={17} />
          </div>
          <DatePicker
            selected={value}
            onChange={(selectedDate: Date | null) => onChange(withDate(value, selectedDate))}
            dateFormat="EEE, MMM d"
            placeholderText={placeholder}
            wrapperClassName="min-w-0 flex-1"
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition-shadow focus:border-slate-400 focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100 dark:focus:ring-slate-800"
            calendarClassName="activity-date-picker"
            popperClassName="z-50 activity-date-picker-popper"
            popperPlacement="bottom-start"
          />
        </div>

        <div className="mt-3 grid gap-3 rounded-md border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100">
            <Clock aria-hidden="true" size={15} />
            {selectedTime.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
          </div>
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <div className="activity-mui-time-clock">
              <TimeClock
                value={selectedTime}
                onChange={(clockValue) => onChange(withClockTime(value, clockValue))}
                ampm
                ampmInClock
                views={['hours', 'minutes']}
              />
            </div>
          </LocalizationProvider>
        </div>

      </div>
    </div>
  )
}

interface ActivityCardProps {
  item: Activity
  onEdit: (item: Activity) => void
  onDelete: (id: string) => Promise<void>
  onDone: (id: string) => Promise<void>
  onUndoDone: (id: string) => Promise<void>
  pastDue?: boolean
}

function ActivityCard({ item, onEdit, onDelete, onDone, onUndoDone, pastDue = false }: ActivityCardProps) {
  const [confirming, setConfirming] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [markingDone, setMarkingDone] = useState(false)
  const [undoingDone, setUndoingDone] = useState(false)

  async function handleDelete() {
    setDeleting(true)
    await onDelete(item.id)
    setDeleting(false)
    setConfirming(false)
  }

  async function handleDone() {
    setMarkingDone(true)
    try {
      await onDone(item.id)
    } finally {
      setMarkingDone(false)
    }
  }

  async function handleUndoDone() {
    setUndoingDone(true)
    try {
      await onUndoDone(item.id)
    } finally {
      setUndoingDone(false)
    }
  }

  return (
    <article
      className={`min-w-0 rounded-lg border bg-white p-4 shadow-sm transition-shadow hover:shadow-md dark:bg-slate-900/50 sm:p-5 ${
        pastDue
          ? 'border-rose-200 ring-1 ring-rose-100 dark:border-rose-900/80 dark:ring-rose-950'
          : 'border-slate-200/60 dark:border-slate-800'
      }`}
    >
      <div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 flex-wrap gap-2">
          <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${kindChipClass(item.activity_kind)}`}>
            {item.activity_kind}
          </span>
          <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusChipClass(item.status)}`}>
            {item.status}
          </span>
          {pastDue && (
            <span className="rounded-full border border-rose-200 bg-rose-100 px-2.5 py-0.5 text-xs font-medium text-rose-700 dark:border-rose-800 dark:bg-rose-900/40 dark:text-rose-300">
              past due
            </span>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-1.5 sm:shrink-0 sm:justify-end">
          {confirming ? (
            <>
              <span className="text-xs text-slate-500 dark:text-slate-400">Delete?</span>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="rounded-md border border-rose-300 bg-rose-50 px-2.5 py-1 text-xs font-medium text-rose-700 transition-colors hover:bg-rose-100 disabled:opacity-60 dark:border-rose-800 dark:bg-rose-950/40 dark:text-rose-300 dark:hover:bg-rose-900/40"
              >
                {deleting ? '...' : 'Yes'}
              </button>
              <button
                onClick={() => setConfirming(false)}
                disabled={deleting}
                className="rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                No
              </button>
            </>
          ) : (
            <>
              {!isDone(item) && (
                <button
                  onClick={handleDone}
                  disabled={markingDone}
                  className="inline-flex items-center gap-1 rounded-md border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 transition-colors hover:bg-emerald-100 disabled:opacity-60 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 dark:hover:bg-emerald-900/40"
                >
                  <Check aria-hidden="true" size={13} />
                  {markingDone ? '...' : 'Done'}
                </button>
              )}
              {isDone(item) && (
                <button
                  onClick={handleUndoDone}
                  disabled={undoingDone}
                  className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 transition-colors hover:border-slate-300 hover:bg-slate-50 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
                >
                  <RotateCcw aria-hidden="true" size={13} />
                  {undoingDone ? '...' : 'Undo'}
                </button>
              )}
              <button
                onClick={() => onEdit(item)}
                className="rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-600 transition-colors hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                Edit
              </button>
              <button
                onClick={() => setConfirming(true)}
                className="rounded-md border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-rose-600 transition-colors hover:border-rose-200 hover:bg-rose-50 dark:border-slate-700 dark:bg-slate-900 dark:text-rose-400 dark:hover:bg-rose-950/30"
              >
                Delete
              </button>
            </>
          )}
        </div>
      </div>
      <h3 className="mb-3 mt-2 break-words text-base font-semibold text-slate-900 dark:text-slate-100">{item.activity_name}</h3>
      <dl className="grid gap-y-1.5 text-sm sm:grid-cols-[120px_1fr]">
        <dt className="text-slate-500 dark:text-slate-400">Start</dt>
        <dd className="break-words text-slate-800 dark:text-slate-200">{formatDateTime(item.start_at)}</dd>
        <dt className="text-slate-500 dark:text-slate-400">Deadline</dt>
        <dd className="break-words text-slate-800 dark:text-slate-200">{formatDateTime(item.deadline_at)}</dd>
        <dt className="text-slate-500 dark:text-slate-400">Offsets (min)</dt>
        <dd className="break-words text-slate-800 dark:text-slate-200">{item.reminder_offsets_minutes?.join(', ') || '-'}</dd>
        <dt className="text-slate-500 dark:text-slate-400">Completed at</dt>
        <dd className="break-words text-slate-800 dark:text-slate-200">{formatDateTime(item.completed_at)}</dd>
      </dl>
    </article>
  )
}

interface SectionProps {
  title: string
  count: number
  accentClass: string
  children: React.ReactNode
  collapsed?: boolean
  onToggle?: () => void
}

function Section({ title, count, accentClass, children, collapsed = false, onToggle }: SectionProps) {
  return (
    <div className="grid gap-3">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex items-center gap-1.5">
          <span className={`break-words text-sm font-semibold tracking-wide ${accentClass}`}>{title}</span>
          {onToggle && (
            <button
              type="button"
              onClick={onToggle}
              aria-label={collapsed ? `Show ${title}` : `Hide ${title}`}
              className="grid h-6 w-6 place-items-center rounded-md text-sm font-semibold text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
            >
              {collapsed ? <ChevronDown aria-hidden="true" size={16} /> : <ChevronUp aria-hidden="true" size={16} />}
            </button>
          )}
        </div>
        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500 dark:bg-slate-800 dark:text-slate-400">
          {count}
        </span>
        <div className="h-px flex-1 bg-slate-200/80 dark:bg-slate-800" />
      </div>
      {!collapsed && children}
    </div>
  )
}

export function ActivitiesPage() {
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [now, setNow] = useState(() => new Date())
  const [hideDoneHabits, setHideDoneHabits] = useState(false)
  const [hidePastDueReminders, setHidePastDueReminders] = useState(false)
  const [hideDoneReminders, setHideDoneReminders] = useState(false)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingActivity, setEditingActivity] = useState<Activity | null>(null)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState<FormState>(() => createInitialForm())

  const { habits, pastDueHabits, doneHabits, reminders, pastDueReminders, doneReminders } = useMemo(() => {
    const activeHabits: Activity[] = []
    const overdueHabits: Activity[] = []
    const completedHabits: Activity[] = []
    const activeReminders: Activity[] = []
    const overdueReminders: Activity[] = []
    const completedReminders: Activity[] = []

    for (const activity of activities) {
      const overdue = isPastDue(activity, now)
      if (activity.activity_kind === 'habit') {
        if (isDone(activity)) completedHabits.push(activity)
        else if (overdue) overdueHabits.push(activity)
        else activeHabits.push(activity)
      } else {
        if (isDone(activity)) completedReminders.push(activity)
        else if (overdue) overdueReminders.push(activity)
        else activeReminders.push(activity)
      }
    }

    return {
      habits: activeHabits,
      pastDueHabits: overdueHabits,
      doneHabits: completedHabits,
      reminders: activeReminders,
      pastDueReminders: overdueReminders,
      doneReminders: completedReminders,
    }
  }, [activities, now])

  async function refresh() {
    try {
      setLoading(true)
      const data = await listActivities()
      setActivities(data)
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load activities')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refresh()
  }, [])

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      setNow(new Date())
    }, 60000)

    return () => window.clearInterval(intervalId)
  }, [])

  function openCreate() {
    setEditingActivity(null)
    setForm(createInitialForm())
    setError('')
    setModalOpen(true)
  }

  function openEdit(item: Activity) {
    setEditingActivity(item)
    setForm(formFromActivity(item))
    setError('')
    setModalOpen(true)
  }

  async function handleDelete(id: string) {
    try {
      await deleteActivity(id)
      setActivities((prev) => prev.filter((a) => a.id !== id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete activity')
    }
  }

  async function handleDone(id: string) {
    try {
      const updated = await updateActivityStatus(id, { status: 'done' })
      setActivities((prev) => prev.map((item) => (item.id === id ? updated : item)))
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to mark activity done')
      throw err
    }
  }

  async function handleUndoDone(id: string) {
    try {
      const updated = await updateActivityStatus(id, { status: 'pending' })
      setActivities((prev) => prev.map((item) => (item.id === id ? updated : item)))
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to undo activity completion')
      throw err
    }
  }

  function closeModal() {
    setModalOpen(false)
    setEditingActivity(null)
    setError('')
  }

  const submit = async (event: FormEvent) => {
    event.preventDefault()

    const offsets = parseOffsets(form.offsets_text)
    if (!form.activity_name.trim()) { setError('Activity name is required'); return }
    if (!form.deadline_at) { setError('Deadline is required'); return }
    if (form.activity_kind === 'habit' && !form.start_at) { setError('Start time is required for habit'); return }
    if (!offsets.length) { setError('Reminder offsets must contain at least one valid minute'); return }

    try {
      setSaving(true)
      if (editingActivity) {
        const payload: ActivityUpdatePayload = {
          activity_name: form.activity_name.trim(),
          deadline_at: toIso(form.deadline_at),
          reminder_offsets_minutes: offsets,
        }
        if (form.start_at) payload.start_at = toIso(form.start_at)
        await updateActivity(editingActivity.id, payload)
      } else {
        const payload: ActivityCreatePayload = {
          activity_name: form.activity_name.trim(),
          activity_kind: form.activity_kind,
          deadline_at: toIso(form.deadline_at),
          reminder_offsets_minutes: offsets,
        }
        if (form.activity_kind === 'habit' && form.start_at) payload.start_at = toIso(form.start_at)
        await createActivity(payload)
      }
      closeModal()
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save activity')
    } finally {
      setSaving(false)
    }
  }

  const isEdit = editingActivity !== null

  return (
    <section className="grid gap-6">
      <article className="flex flex-col gap-4 rounded-lg border border-slate-200/60 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/50 sm:flex-row sm:items-center sm:justify-between sm:p-5">
        <div className="min-w-0">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Activities & Habits</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {habits.length + pastDueHabits.length + doneHabits.length} habit{habits.length + pastDueHabits.length + doneHabits.length !== 1 ? 's' : ''} · {reminders.length + pastDueReminders.length + doneReminders.length} reminder{reminders.length + pastDueReminders.length + doneReminders.length !== 1 ? 's' : ''} · {pastDueHabits.length + pastDueReminders.length} past due
          </p>
        </div>
        <button
          className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100 sm:w-auto"
          onClick={openCreate}
        >
          + Add activity
        </button>
      </article>

      {error && !modalOpen ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-5 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">
          {error}
        </div>
      ) : null}

      {loading ? (
        <div className="rounded-lg border border-slate-200/60 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900/50">
          <span className="text-sm text-slate-500">Loading activities...</span>
        </div>
      ) : (
        <div className="grid gap-8">
          {/* ── Habits ── */}
          <Section title="Upcoming Habits" count={habits.length} accentClass="text-violet-600 dark:text-violet-400">
            {habits.length === 0 ? (
              <p className="text-sm text-slate-400 dark:text-slate-500">No upcoming habits.</p>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {habits.map((item) => (
                  <ActivityCard key={item.id} item={item} onEdit={openEdit} onDelete={handleDelete} onDone={handleDone} onUndoDone={handleUndoDone} />
                ))}
              </div>
            )}
          </Section>

          <Section title="Past Due Habits" count={pastDueHabits.length} accentClass="text-rose-600 dark:text-rose-400">
            {pastDueHabits.length === 0 ? (
              <p className="text-sm text-slate-400 dark:text-slate-500">No habits are past their time span.</p>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {pastDueHabits.map((item) => (
                  <ActivityCard key={item.id} item={item} onEdit={openEdit} onDelete={handleDelete} onDone={handleDone} onUndoDone={handleUndoDone} pastDue />
                ))}
              </div>
            )}
          </Section>

          <Section
            title="Done Habits"
            count={doneHabits.length}
            accentClass="text-emerald-600 dark:text-emerald-400"
            collapsed={hideDoneHabits}
            onToggle={() => setHideDoneHabits((value) => !value)}
          >
            {doneHabits.length === 0 ? (
              <p className="text-sm text-slate-400 dark:text-slate-500">No completed habits.</p>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {doneHabits.map((item) => (
                  <ActivityCard key={item.id} item={item} onEdit={openEdit} onDelete={handleDelete} onDone={handleDone} onUndoDone={handleUndoDone} />
                ))}
              </div>
            )}
          </Section>

          {/* ── Reminders ── */}
          <Section title="Upcoming Reminders" count={reminders.length} accentClass="text-blue-600 dark:text-blue-400">
            {reminders.length === 0 ? (
              <p className="text-sm text-slate-400 dark:text-slate-500">No upcoming reminders.</p>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {reminders.map((item) => (
                  <ActivityCard key={item.id} item={item} onEdit={openEdit} onDelete={handleDelete} onDone={handleDone} onUndoDone={handleUndoDone} />
                ))}
              </div>
            )}
          </Section>

          <Section
            title="Past Due Reminders"
            count={pastDueReminders.length}
            accentClass="text-rose-600 dark:text-rose-400"
            collapsed={hidePastDueReminders}
            onToggle={() => setHidePastDueReminders((value) => !value)}
          >
            {pastDueReminders.length === 0 ? (
              <p className="text-sm text-slate-400 dark:text-slate-500">No reminders are past their deadline.</p>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {pastDueReminders.map((item) => (
                  <ActivityCard key={item.id} item={item} onEdit={openEdit} onDelete={handleDelete} onDone={handleDone} onUndoDone={handleUndoDone} pastDue />
                ))}
              </div>
            )}
          </Section>

          <Section
            title="Done Reminders"
            count={doneReminders.length}
            accentClass="text-emerald-600 dark:text-emerald-400"
            collapsed={hideDoneReminders}
            onToggle={() => setHideDoneReminders((value) => !value)}
          >
            {doneReminders.length === 0 ? (
              <p className="text-sm text-slate-400 dark:text-slate-500">No completed reminders.</p>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {doneReminders.map((item) => (
                  <ActivityCard key={item.id} item={item} onEdit={openEdit} onDelete={handleDelete} onDone={handleDone} onUndoDone={handleUndoDone} />
                ))}
              </div>
            )}
          </Section>
        </div>
      )}

      {modalOpen && (
        <div
          className="fixed inset-0 z-20 grid place-items-center overflow-y-auto bg-black/50 p-2 backdrop-blur-sm sm:p-4"
          onClick={closeModal}
        >
          <div
            className="my-2 flex max-h-[calc(100dvh-1rem)] w-full max-w-lg flex-col overflow-hidden rounded-xl border border-slate-200/60 bg-white shadow-xl dark:border-slate-800 dark:bg-slate-900 sm:my-6 sm:max-h-[calc(100dvh-3rem)]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="border-b border-slate-200/70 px-4 py-4 dark:border-slate-800 sm:px-6 sm:py-5">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                {isEdit ? `Edit ${editingActivity!.activity_kind}` : 'Add activity'}
              </h3>
            </div>

            <form className="flex min-h-0 flex-1 flex-col" onSubmit={submit}>
              <div className="grid gap-4 overflow-y-auto px-4 py-4 sm:px-6 sm:py-5">
                {error && (
                  <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">
                    {error}
                  </div>
                )}

              <label className="grid gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-300">
                {isEdit ? (form.activity_kind === 'habit' ? 'Habit' : 'Activity') : 'Activity'} name
                <input
                  className={inputClass}
                  value={form.activity_name}
                  onChange={(e) => setForm((prev) => ({ ...prev, activity_name: e.target.value }))}
                  placeholder="e.g. Morning workout"
                />
              </label>

              {/* Type selector only shown when creating */}
              {!isEdit && (
                <label className="grid gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-300">
                  Type
                  <select
                    className={inputClass}
                    value={form.activity_kind}
                    onChange={(e) =>
                      setForm((prev) => ({ ...prev, activity_kind: e.target.value as ActivityKind }))
                    }
                  >
                    <option value="habit">Habit</option>
                    <option value="reminder">Reminder</option>
                  </select>
                </label>
              )}

              {form.activity_kind === 'habit' && (
                <SchedulePicker
                  label="Start schedule"
                  value={form.start_at}
                  onChange={(value) => setForm((prev) => ({ ...prev, start_at: value }))}
                  placeholder="Choose start date and time"
                />
              )}

              <SchedulePicker
                label="Deadline schedule"
                value={form.deadline_at}
                onChange={(value) => setForm((prev) => ({ ...prev, deadline_at: value }))}
                placeholder="Choose deadline date and time"
              />

              <label className="grid gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-300">
                Reminder offsets (minutes)
                <input
                  className={inputClass}
                  value={form.offsets_text}
                  onChange={(e) => setForm((prev) => ({ ...prev, offsets_text: e.target.value }))}
                  placeholder="30, 60"
                />
              </label>

              </div>

              <div className="sticky bottom-0 flex flex-col-reverse gap-2 border-t border-slate-200/70 bg-white px-4 py-4 dark:border-slate-800 dark:bg-slate-900 sm:flex-row sm:justify-end sm:px-6">
                <button
                  type="button"
                  className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                  onClick={closeModal}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100"
                  disabled={saving}
                >
                  {saving ? 'Saving...' : isEdit ? 'Save changes' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  )
}
