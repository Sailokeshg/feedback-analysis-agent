import { useEffect, lazy, Suspense } from 'react';
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

function App() {
  const { fetchFeedback, fetchTopics, fetchTrends } = useFeedbackStore();
  const { fetchDashboardSummary } = useDashboardStore();

  useEffect(() => {
    // Initial data load - load in parallel to avoid blocking
    Promise.all([
      fetchFeedback(),
      fetchTopics(),
      fetchTrends(),
      fetchDashboardSummary(),
    ]).catch((error) => {
      console.error('Failed to load initial data:', error);
    });
  }, [fetchFeedback, fetchTopics, fetchTrends, fetchDashboardSummary]);

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
