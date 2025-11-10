import { useEffect, useState, lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useFeedbackStore } from './stores/feedbackStore';
import { useDashboardStore } from './stores/dashboardStore';
import Layout from './components/Layout';

// Lazy load pages for better performance
const Dashboard = lazy(() => import('./components/Dashboard'));
const TopicsPage = lazy(() => import('./pages/TopicsPage'));
const TopicDetail = lazy(() => import('./pages/TopicDetail'));
const ExplorerPage = lazy(() => import('./pages/ExplorerPage'));
const AdminTopicsPage = lazy(() => import('./pages/AdminTopicsPage'));

// Loading component for suspense fallback
const PageLoading = () => (
  <div className="flex items-center justify-center min-h-[400px]">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
  </div>
);

// Initial loading component
const InitialLoading = () => (
  <div className="min-h-screen bg-white dark:bg-gray-900 flex items-center justify-center">
    <div className="text-center">
      <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
      <div className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Loading AI Customer Insights</div>
      <div className="text-gray-600 dark:text-gray-400">Initializing application...</div>
    </div>
  </div>
);

// Error component for initial load failure
const InitialLoadError = ({ onRetry }: { onRetry: () => void }) => (
  <div className="min-h-screen bg-white dark:bg-gray-900 flex items-center justify-center">
    <div className="text-center max-w-md mx-auto px-4">
      <div className="text-red-600 dark:text-red-400 text-6xl mb-4">⚠️</div>
      <div className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Failed to Load Application</div>
      <div className="text-gray-600 dark:text-gray-400 mb-6">
        Unable to connect to the backend services. Please check that the server is running.
      </div>
      <button
        onClick={onRetry}
        className="inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-blue-600 text-white hover:bg-blue-700 h-10 px-4 py-2"
      >
        Try Again
      </button>
    </div>
  </div>
);

function App() {
  const { fetchFeedback, fetchTopics, fetchTrends } = useFeedbackStore();
  const { fetchDashboardSummary } = useDashboardStore();
  const [initialLoading, setInitialLoading] = useState(true);
  const [initialLoadError, setInitialLoadError] = useState<string | null>(null);

  const loadInitialData = async () => {
    setInitialLoading(true);
    setInitialLoadError(null);

    try {
      // Initial data load - load in parallel to avoid blocking
      await Promise.all([
        fetchFeedback(),
        fetchTopics(),
        fetchTrends(),
        fetchDashboardSummary(),
      ]);
      setInitialLoading(false);
    } catch (error) {
      console.error('Failed to load initial data:', error);
      setInitialLoadError(error instanceof Error ? error.message : 'Unknown error occurred');
      setInitialLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []); // Only run once on mount

  // Show initial loading state
  if (initialLoading) {
    return <InitialLoading />;
  }

  // Show error state if initial load failed
  if (initialLoadError) {
    return <InitialLoadError onRetry={loadInitialData} />;
  }

  return (
    <Layout>
      <Suspense fallback={<PageLoading />}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/topics" element={<TopicsPage />} />
          <Route path="/topics/:topicId" element={<TopicDetail />} />
          <Route path="/explorer" element={<ExplorerPage />} />
          <Route path="/admin/topics" element={<AdminTopicsPage />} />
        </Routes>
      </Suspense>
    </Layout>
  );
}

export default App;
