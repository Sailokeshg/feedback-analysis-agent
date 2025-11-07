import { ReactNode, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useThemeStore } from '../stores/themeStore'
import ChatPanel from './ChatPanel'

interface LayoutProps {
  children: ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  const { isDark, toggleTheme } = useThemeStore()
  const location = useLocation()

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDark])

  const navigation = [
    { name: 'Dashboard', href: '/' },
    { name: 'Topics', href: '/topics' },
    { name: 'Explorer', href: '/explorer' },
  ]

  return (
    <div className="min-h-screen bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b border-gray-200 dark:border-gray-800 bg-white/95 dark:bg-gray-900/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:supports-[backdrop-filter]:bg-gray-900/60">
        <div className="container flex h-14 items-center px-4">
          <div className="mr-4 flex">
            <Link to="/" className="text-xl font-bold hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
              AI Customer Insights
            </Link>
          </div>
          <nav className="flex items-center space-x-6">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`text-sm font-medium transition-colors hover:text-blue-600 dark:hover:text-blue-400 ${
                  location.pathname === item.href
                    ? 'text-blue-600 dark:text-blue-400'
                    : 'text-gray-900 dark:text-gray-100'
                }`}
              >
                {item.name}
              </Link>
            ))}
          </nav>
          <div className="flex flex-1 items-center justify-end space-x-2">
            <button
              onClick={toggleTheme}
              className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 h-9 px-3"
              aria-label="Toggle theme"
            >
              {isDark ? '☀️' : '🌙'}
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="container mx-auto px-4 py-6">
        {children}
      </main>

      {/* Chat Panel */}
      <ChatPanel />
    </div>
  )
}

export default Layout
