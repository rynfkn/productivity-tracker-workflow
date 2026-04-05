import { useEffect, useMemo, useState } from 'react'
import { ActivitiesPage } from './pages/ActivitiesPage.tsx'
import { DashboardPage } from './pages/DashboardPage.tsx'

type AppRoute = '/dashboard' | '/activities'

function getRouteFromPath(pathname: string): AppRoute {
  if (pathname.startsWith('/activities')) return '/activities'
  return '/dashboard'
}

function App() {
  const [route, setRoute] = useState<AppRoute>(
    getRouteFromPath(window.location.pathname),
  )

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
      </header>

      <main>
        {route === '/dashboard' ? <DashboardPage /> : <ActivitiesPage />}
      </main>
    </div>
  )
}

export default App

