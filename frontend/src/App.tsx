import { useEffect, useMemo, useState } from 'react'
import { ActivitiesPage } from './pages/ActivitiesPage.tsx'
import { DashboardPage } from './pages/DashboardPage.tsx'

type AppRoute = '/dashboard' | '/activities'
type Theme = 'light' | 'dark'

function getRouteFromPath(pathname: string): AppRoute {
  if (pathname.startsWith('/activities')) return '/activities'
  return '/dashboard'
}

function getInitialTheme(): Theme {
  const stored = localStorage.getItem('theme')
  if (stored === 'light' || stored === 'dark') return stored
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function SunIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  )
}

function MoonIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
    </svg>
  )
}

function App() {
  const [route, setRoute] = useState<AppRoute>(
    getRouteFromPath(window.location.pathname),
  )
  const [theme, setTheme] = useState<Theme>(getInitialTheme)

  useEffect(() => {
    const root = document.documentElement
    if (theme === 'dark') {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    localStorage.setItem('theme', theme)
  }, [theme])

  useEffect(() => {
    const onPopState = () => setRoute(getRouteFromPath(window.location.pathname))
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [])

  const navigate = (next: AppRoute) => {
    if (route === next) return
    window.history.pushState({}, '', next)
    setRoute(next)
  }

  const title = useMemo(() => {
    return route === '/dashboard' ? 'Overview' : 'Activities & Habits'
  }, [route])

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <header className="mb-8 flex flex-col gap-6 sm:flex-row sm:items-end justify-between border-b border-slate-200/60 pb-5 dark:border-slate-800/60">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900 dark:text-white">Productivity</h1>
          <p className="mt-1 text-sm font-medium text-slate-500 dark:text-slate-400">{title}</p>
        </div>
        <div className="flex items-center gap-2">
          <nav className="flex space-x-1 rounded-lg bg-slate-100/80 p-1 dark:bg-slate-800/80" aria-label="Main navigation">
            <button
              className={`flex items-center rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                route === '/dashboard'
                  ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-white'
                  : 'text-slate-500 hover:bg-white/50 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-700/50 dark:hover:text-slate-300'
              }`}
              onClick={() => navigate('/dashboard')}
            >
              Dashboard
            </button>
            <button
              className={`flex items-center rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                route === '/activities'
                  ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-white'
                  : 'text-slate-500 hover:bg-white/50 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-700/50 dark:hover:text-slate-300'
              }`}
              onClick={() => navigate('/activities')}
            >
              Activities
            </button>
          </nav>
          <button
            onClick={() => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))}
            aria-label="Toggle theme"
            className="flex h-[34px] w-[34px] items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition-colors hover:border-slate-300 hover:bg-slate-50 hover:text-slate-700 dark:border-slate-700 dark:bg-slate-800/80 dark:text-slate-400 dark:hover:border-slate-600 dark:hover:bg-slate-700 dark:hover:text-slate-200"
          >
            {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
          </button>
        </div>
      </header>

      <main>
        {route === '/dashboard' ? <DashboardPage /> : <ActivitiesPage />}
      </main>
    </div>
  )
}

export default App

