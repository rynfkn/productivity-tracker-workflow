import { useEffect, useMemo, useState } from 'react'
import { getCompletions, getHabitProgress, getTodayProgress } from '../api'
import type { Activity, HabitProgress, ProgressSummary } from '../types'

interface HeatDay {
  dateKey: string
  date: Date
  count: number
  inFuture: boolean
  level: 0 | 1 | 2 | 3 | 4
}

interface HeatWeek {
  days: HeatDay[]
  monthLabel: string | null
}

function toDateKey(date: Date) {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

function intensityLevel(count: number, max: number): 0 | 1 | 2 | 3 | 4 {
  if (count <= 0) return 0
  if (max <= 1) return 4
  const ratio = count / max
  if (ratio <= 0.25) return 1
  if (ratio <= 0.5) return 2
  if (ratio <= 0.75) return 3
  return 4
}

function heatClass(level: 0 | 1 | 2 | 3 | 4): string {
  if (level === 0) return 'bg-[#ebedf0] dark:bg-[#161b22]'
  if (level === 1) return 'bg-[#9be9a8] dark:bg-[#0e4429]'
  if (level === 2) return 'bg-[#40c463] dark:bg-[#006d32]'
  if (level === 3) return 'bg-[#30a14e] dark:bg-[#26a641]'
  return 'bg-[#216e39] dark:bg-[#39d353]'
}

function buildHeatWeeks(activities: Activity[]): HeatWeek[] {
  const completedByDay = new Map<string, number>()

  for (const activity of activities) {
    if (!activity.completed_at) continue
    const key = toDateKey(new Date(activity.completed_at))
    completedByDay.set(key, (completedByDay.get(key) || 0) + 1)
  }

  const maxCount = Math.max(
    1,
    Array.from(completedByDay.values()).reduce((a, b) => Math.max(a, b), 0),
  )

  const today = startOfDay(new Date())
  const todayDay = today.getDay()
  const endOfThisWeek = new Date(today)
  endOfThisWeek.setDate(today.getDate() + (6 - todayDay)) // Saturday of current week

  const columns = 53 // 52 full weeks + current week
  const startOfGraph = new Date(endOfThisWeek)
  startOfGraph.setDate(endOfThisWeek.getDate() - columns * 7 + 1)

  const weeks: HeatWeek[] = []
  const cursor = new Date(startOfGraph)
  let currentMonth = -1

  for (let w = 0; w < columns; w++) {
    const weekDays: HeatDay[] = []
    let monthLabel = null

    for (let d = 0; d < 7; d++) {
      const key = toDateKey(cursor)
      const inFuture = cursor > today
      const count = inFuture ? 0 : completedByDay.get(key) || 0
      weekDays.push({
        dateKey: key,
        date: new Date(cursor),
        count,
        inFuture,
        level: inFuture ? 0 : intensityLevel(count, maxCount),
      })
      cursor.setDate(cursor.getDate() + 1)
    }

    // Assign month label if the month changed in the first day of the week, or it's the first week
    const month = weekDays[0].date.getMonth()
    if (month !== currentMonth) {
      if (w > 0 || weekDays[0].date.getDate() <= 7) {
        monthLabel = weekDays[0].date.toLocaleString('default', { month: 'short' })
      }
      currentMonth = month
    }

    weeks.push({ days: weekDays, monthLabel })
  }

  return weeks
}

export function DashboardPage() {
  const [activities, setActivities] = useState<Activity[]>([])
  const [today, setToday] = useState<ProgressSummary | null>(null)
  const [habitProgress, setHabitProgress] = useState<HabitProgress[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  useEffect(() => {
    let active = true

    async function load(silent = false) {
      try {
        if (!silent) setLoading(true)
        const [completionsData, todayData, habitData] = await Promise.all([
          getCompletions(),
          getTodayProgress(),
          getHabitProgress(),
        ])
        if (!active) return
        setActivities(completionsData)
        setToday(todayData)
        setHabitProgress(habitData)
        setError('')
      } catch (err) {
        if (!active) return
        setError(err instanceof Error ? err.message : 'Failed to load dashboard')
      } finally {
        if (active && !silent) setLoading(false)
      }
    }

    void load()

    const onFocus = () => {
      void load(true)
    }

    const intervalId = window.setInterval(() => {
      void load(true)
    }, 30000)

    window.addEventListener('focus', onFocus)

    return () => {
      active = false
      window.clearInterval(intervalId)
      window.removeEventListener('focus', onFocus)
    }
  }, [])

  const weeks = useMemo(() => buildHeatWeeks(activities), [activities])

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center rounded-lg border border-slate-200/60 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900/50">
        <span className="text-sm text-slate-500">Loading dashboard...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-5 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
        {error}
      </div>
    )
  }

  return (
    <section className="grid gap-6">
      <div className="grid gap-4 md:grid-cols-3">
        <article className="flex flex-col justify-between rounded-lg border border-slate-200/60 bg-white p-5 shadow-sm transition-shadow hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
            Completed Today
          </p>
          <p className="mt-2 text-4xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
            {today?.total_completed ?? 0}
          </p>
        </article>
        <article className="flex flex-col justify-between rounded-lg border border-slate-200/60 bg-white p-5 shadow-sm transition-shadow hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
            Planned Today
          </p>
          <p className="mt-2 text-4xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
            {today?.total_planned ?? 0}
          </p>
        </article>
        <article className="flex flex-col justify-between rounded-lg border border-slate-200/60 bg-white p-5 shadow-sm transition-shadow hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50">
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
            Completion Rate
          </p>
          <p className="mt-2 text-4xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">
            {Math.round((today?.completion_rate ?? 0) * 100)}%
          </p>
        </article>
      </div>

      <article className="rounded-lg border border-slate-200/60 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900/50">
        <div className="mb-6">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
            Contribution Activity
          </h2>
          <p className="mb-2 mt-1 text-sm text-slate-500 dark:text-slate-400">
            Track your habits and activities over the past year.
          </p>
        </div>

        <div className="overflow-x-auto pb-4">
          <div className="flex w-fit min-w-full gap-1">
            {/* Y-Axis Labels: Mon, Wed, Fri */}
            <div className="flex flex-col gap-[3px] pt-[20px] pr-2 text-[10px] leading-[10px] text-slate-400 dark:text-slate-500">
              <span className="invisible h-[10px]" aria-hidden>Sun</span>
              <span className="h-[10px]">Mon</span>
              <span className="invisible h-[10px]" aria-hidden>Tue</span>
              <span className="h-[10px]">Wed</span>
              <span className="invisible h-[10px]" aria-hidden>Thu</span>
              <span className="h-[10px]">Fri</span>
              <span className="invisible h-[10px]" aria-hidden>Sat</span>
            </div>

            {/* The 53 weeks grid */}
            {weeks.map((week, wIndex) => (
              <div key={wIndex} className="relative flex flex-col gap-[3px]">
                {/* Month Label Header */}
                <div className="h-[20px]">
                  {week.monthLabel && (
                    <span className="absolute left-0 top-0 whitespace-nowrap text-[10px] text-slate-400 dark:text-slate-500">
                      {week.monthLabel}
                    </span>
                  )}
                </div>

                {/* 7 Days of the week */}
                {week.days.map((day) => (
                  <div
                    key={day.dateKey}
                    className={`h-[10px] w-[10px] rounded-[2px] ${
                      day.inFuture ? 'bg-transparent' : heatClass(day.level)
                    } ${!day.inFuture && 'outline outline-1 outline-offset-[-1px] outline-black/5 dark:outline-white/5'}`}
                    title={
                      day.inFuture
                        ? undefined
                        : `${day.count === 0 ? 'No' : day.count} activities on ${day.date.toLocaleString(
                            'default',
                            { month: 'short', day: 'numeric', year: 'numeric' },
                          )}`
                    }
                  />
                ))}
              </div>
            ))}
          </div>
        </div>

        <div className="mt-4 flex items-center justify-end gap-1.5 text-xs text-slate-500 dark:text-slate-400">
          <span className="px-1">Less</span>
          <span className={`h-[10px] w-[10px] rounded-[2px] ${heatClass(0)} outline outline-1 outline-offset-[-1px] outline-black/5 dark:outline-white/5`} />
          <span className={`h-[10px] w-[10px] rounded-[2px] ${heatClass(1)} outline outline-1 outline-offset-[-1px] outline-black/5 dark:outline-white/5`} />
          <span className={`h-[10px] w-[10px] rounded-[2px] ${heatClass(2)} outline outline-1 outline-offset-[-1px] outline-black/5 dark:outline-white/5`} />
          <span className={`h-[10px] w-[10px] rounded-[2px] ${heatClass(3)} outline outline-1 outline-offset-[-1px] outline-black/5 dark:outline-white/5`} />
          <span className={`h-[10px] w-[10px] rounded-[2px] ${heatClass(4)} outline outline-1 outline-offset-[-1px] outline-black/5 dark:outline-white/5`} />
          <span className="px-1">More</span>
        </div>
      </article>

      <article className="rounded-lg border border-slate-200/60 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900/50">
        <div className="mb-5">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Habit Progress</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Lifetime done vs missed count for each habit.
          </p>
        </div>

        {habitProgress.length === 0 ? (
          <p className="text-sm text-slate-400 dark:text-slate-500">No habit data yet. Complete or miss a habit to see progress here.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs font-medium uppercase tracking-wide text-slate-400 dark:border-slate-800 dark:text-slate-500">
                  <th className="pb-3 pr-4">Habit</th>
                  <th className="pb-3 pr-4 text-right">Done</th>
                  <th className="pb-3 pr-4 text-right">Missed</th>
                  <th className="pb-3 pr-4 text-right">Total</th>
                  <th className="pb-3 min-w-[120px]">Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {habitProgress.map((h) => {
                  const rate = h.total > 0 ? Math.round((h.done / h.total) * 100) : 0
                  return (
                    <tr key={h.habit_name} className="group">
                      <td className="py-3 pr-4 font-medium text-slate-800 dark:text-slate-200">{h.habit_name}</td>
                      <td className="py-3 pr-4 text-right text-emerald-600 dark:text-emerald-400">{h.done}</td>
                      <td className="py-3 pr-4 text-right text-orange-500 dark:text-orange-400">{h.missed}</td>
                      <td className="py-3 pr-4 text-right text-slate-500 dark:text-slate-400">{h.total}</td>
                      <td className="py-3">
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                            <div
                              className="h-full rounded-full bg-emerald-500 dark:bg-emerald-400 transition-all"
                              style={{ width: `${rate}%` }}
                            />
                          </div>
                          <span className="w-9 text-right text-xs text-slate-500 dark:text-slate-400">{rate}%</span>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </article>
    </section>
  )
}

