import { ReactNode, useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useThemeStore } from '../stores/themeStore'
import { useAdminStore } from '../stores/adminStore'
import ChatPanel from './ChatPanel'
import AdminLogin from './AdminLogin'

interface LayoutProps {
  children: ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  const { isDark, toggleTheme } = useThemeStore()
  const { isAuthenticated, user, logout, checkAuth } = useAdminStore()
  const location = useLocation()
  const [showAdminLogin, setShowAdminLogin] = useState(false)

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDark])

  useEffect(() => {
    // Check auth status on mount
    checkAuth()
  }, [checkAuth])

  const navigation = [
    { name: 'Dashboard', href: '/' },
    { name: 'Topics', href: '/topics' },
    { name: 'Explorer', href: '/explorer' },
  ]

  const adminNavigation = [
    { name: 'Topic Management', href: '/admin/topics' },
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

            {/* Admin Navigation */}
            {isAuthenticated && (
              <>
                <div className="h-4 w-px bg-gray-300 dark:bg-gray-600"></div>
                {adminNavigation.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`text-sm font-medium transition-colors hover:text-orange-600 dark:hover:text-orange-400 ${
                      location.pathname === item.href
                        ? 'text-orange-600 dark:text-orange-400'
                        : 'text-gray-900 dark:text-gray-100'
                    }`}
                  >
                    {item.name}
                  </Link>
                ))}
              </>
            )}
          </nav>

          <div className="flex flex-1 items-center justify-end space-x-2">
            {/* Admin Status */}
            {isAuthenticated ? (
              <div className="flex items-center space-x-3">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-medium">{user?.username}</span>
                  <span className="ml-1 px-2 py-0.5 text-xs bg-orange-100 dark:bg-orange-900/20 text-orange-800 dark:text-orange-300 rounded">
                    {user?.role}
                  </span>
                </div>
                <button
                  onClick={logout}
                  className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-red-300 dark:border-red-600 bg-white dark:bg-gray-800 text-red-700 dark:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 h-9 px-3"
                >
                  Logout
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowAdminLogin(true)}
                className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-orange-300 dark:border-orange-600 bg-white dark:bg-gray-800 text-orange-700 dark:text-orange-300 hover:bg-orange-50 dark:hover:bg-orange-900/20 h-9 px-3"
              >
                Admin Login
              </button>
            )}

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

      {/* Admin Login Modal */}
      <AdminLogin
        isOpen={showAdminLogin}
        onClose={() => setShowAdminLogin(false)}
      />
    </div>
  )
}

export default Layout
