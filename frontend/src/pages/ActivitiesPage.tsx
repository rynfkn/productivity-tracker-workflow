import { type FormEvent, useEffect, useMemo, useState } from 'react'
import DatePicker from 'react-datepicker'
import 'react-datepicker/dist/react-datepicker.css'
import { createActivity, listActivities } from '../api'
import type { Activity, ActivityCreatePayload, ActivityKind } from '../types'

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

function formatDateTime(value: string | null) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

function toIso(date: Date): string {
  return date.toISOString()
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
  if (status === 'done') {
    return 'border-emerald-200 bg-emerald-100 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300'
  }
  if (status === 'failed') {
    return 'border-rose-200 bg-rose-100 text-rose-700 dark:border-rose-800 dark:bg-rose-900/40 dark:text-rose-300'
  }
  return 'border-amber-200 bg-amber-100 text-amber-700 dark:border-amber-800 dark:bg-amber-900/40 dark:text-amber-300'
}

export function ActivitiesPage() {
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState<FormState>(() => createInitialForm())

  const pendingCount = useMemo(
    () => activities.filter((item) => item.status === 'pending').length,
    [activities],
  )

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

  const submit = async (event: FormEvent) => {
    event.preventDefault()

    const offsets = parseOffsets(form.offsets_text)
    if (!form.activity_name.trim()) {
      setError('Activity name is required')
      return
    }
    if (!form.deadline_at) {
      setError('Deadline is required')
      return
    }
    if (form.activity_kind === 'habit' && !form.start_at) {
      setError('Start time is required for habit')
      return
    }
    if (!offsets.length) {
      setError('Reminder offsets must contain at least one valid minute')
      return
    }

    const payload: ActivityCreatePayload = {
      activity_name: form.activity_name.trim(),
      activity_kind: form.activity_kind,
      deadline_at: toIso(form.deadline_at),
      reminder_offsets_minutes: offsets,
    }

    if (form.activity_kind === 'habit' && form.start_at) {
      payload.start_at = toIso(form.start_at)
    }

    try {
      setSaving(true)
      await createActivity(payload)
      setModalOpen(false)
      setForm(createInitialForm())
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create activity')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="grid gap-4">
      <article className="flex items-center justify-between rounded-lg border border-slate-200/60 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900/50">
        <div>
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">All activities and habits</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {activities.length} total · {pendingCount} pending
          </p>
        </div>
        <button
          className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-slate-800 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100"
          onClick={() => setModalOpen(true)}
        >
          + Add activity
        </button>
      </article>

      {error ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-5 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">
          {error}
        </div>
      ) : null}
      {loading ? (
        <div className="rounded-lg border border-slate-200/60 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900/50">
          <span className="text-sm text-slate-500">Loading activities...</span>
        </div>
      ) : null}

      {!loading && (
        <div className="grid gap-4 md:grid-cols-2">
          {activities.map((item) => (
            <article
              key={item.id}
              className="rounded-lg border border-slate-200/60 bg-white p-5 shadow-sm transition-shadow hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50"
            >
              <div className="flex gap-2">
                <span
                  className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${kindChipClass(item.activity_kind)}`}
                >
                  {item.activity_kind}
                </span>
                <span
                  className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusChipClass(item.status)}`}
                >
                  {item.status}
                </span>
              </div>
              <h3 className="mb-3 mt-2 text-base font-semibold">{item.activity_name}</h3>
              <dl className="grid grid-cols-[120px_1fr] gap-y-1.5 text-sm">
                <dt className="text-slate-500 dark:text-slate-400">Start</dt>
                <dd>{formatDateTime(item.start_at)}</dd>
                <dt className="text-slate-500 dark:text-slate-400">Deadline</dt>
                <dd>{formatDateTime(item.deadline_at)}</dd>
                <dt className="text-slate-500 dark:text-slate-400">Offsets (min)</dt>
                <dd>{item.reminder_offsets_minutes?.join(', ') || '-'}</dd>
                <dt className="text-slate-500 dark:text-slate-400">Completed at</dt>
                <dd>{formatDateTime(item.completed_at)}</dd>
              </dl>
            </article>
          ))}
        </div>
      )}

      {modalOpen && (
        <div
          className="fixed inset-0 z-20 grid place-items-center bg-black/50 p-4 backdrop-blur-sm"
          onClick={() => setModalOpen(false)}
        >
          <div
            className="w-full max-w-lg rounded-xl border border-slate-200/60 bg-white p-6 shadow-xl dark:border-slate-800 dark:bg-slate-900"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="mb-5 text-lg font-semibold text-slate-900 dark:text-slate-100">Add activity</h3>
            <form className="grid gap-4" onSubmit={submit}>
              <label className="grid gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-300">
                Activity name
                <input
                  className="rounded-md border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition-shadow focus:border-slate-400 focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:focus:ring-slate-800 text-slate-900 dark:text-slate-100"
                  value={form.activity_name}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, activity_name: e.target.value }))
                  }
                  placeholder="e.g. Morning workout"
                />
              </label>

              <label className="grid gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-300">
                Type
                <select
                  className="rounded-md border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition-shadow focus:border-slate-400 focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:focus:ring-slate-800 text-slate-900 dark:text-slate-100"
                  value={form.activity_kind}
                  onChange={(e) =>
                    setForm((prev) => ({
                      ...prev,
                      activity_kind: e.target.value as ActivityKind,
                    }))
                  }
                >
                  <option value="habit">Habit</option>
                  <option value="reminder">Reminder</option>
                </select>
              </label>

              {form.activity_kind === 'habit' && (
                <label className="grid gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-300">
                  Start schedule
                  <DatePicker
                    selected={form.start_at}
                    onChange={(value: Date | null) =>
                      setForm((prev) => ({ ...prev, start_at: value }))
                    }
                    showTimeSelect
                    timeIntervals={15}
                    timeCaption="Time"
                    dateFormat="PPpp"
                    placeholderText="Choose start date and time"
                    className="w-full rounded-md border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition-shadow focus:border-slate-400 focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                    popperClassName="z-50"
                  />
                </label>
              )}

              <label className="grid gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-300">
                Deadline schedule
                <DatePicker
                  selected={form.deadline_at}
                  onChange={(value: Date | null) =>
                    setForm((prev) => ({ ...prev, deadline_at: value }))
                  }
                  showTimeSelect
                  timeIntervals={15}
                  timeCaption="Time"
                  dateFormat="PPpp"
                  placeholderText="Choose deadline date and time"
                  className="w-full rounded-md border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition-shadow focus:border-slate-400 focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-100"
                  minDate={new Date()}
                  popperClassName="z-50"
                />
              </label>

              <label className="grid gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-300">
                Reminder offsets (minutes)
                <input
                  className="rounded-md border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition-shadow focus:border-slate-400 focus:ring-2 focus:ring-slate-200 dark:border-slate-700 dark:bg-slate-950 dark:focus:ring-slate-800 text-slate-900 dark:text-slate-100"
                  value={form.offsets_text}
                  onChange={(e) =>
                    setForm((prev) => ({ ...prev, offsets_text: e.target.value }))
                  }
                  placeholder="30,45"
                />
              </label>

              <div className="mt-2 flex justify-end gap-2">
                <button
                  type="button"
                  className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                  onClick={() => setModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100"
                  disabled={saving}
                >
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  )
}
