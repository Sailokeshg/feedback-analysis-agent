import { useEffect } from 'react';
import { useFeedbackStore } from '../stores/feedbackStore';
import { useDashboardStore } from '../stores/dashboardStore';
import { ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, Tooltip, CartesianGrid, XAxis, YAxis } from 'recharts';
import KPICards from './KPICards';
import TrendChart from './TrendChart';
import TopNegativeTopics from './TopNegativeTopics';
import DateRangeFilter from './DateRangeFilter';

const Dashboard = () => {
  const { feedbackItems, topicClusters, isLoading, error } = useFeedbackStore();
  const { fetchDashboardSummary } = useDashboardStore();

  // Initialize dashboard data on mount
  useEffect(() => {
    fetchDashboardSummary();
  }, [fetchDashboardSummary]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="text-red-600 dark:text-red-400 text-lg font-semibold mb-2">Error</div>
          <div className="text-gray-600 dark:text-gray-400">{error}</div>
        </div>
      </div>
    );
  }

  const sentimentData = [
    { name: 'Positive', value: feedbackItems.filter(f => f.sentiment === 'positive').length },
    { name: 'Negative', value: feedbackItems.filter(f => f.sentiment === 'negative').length },
    { name: 'Neutral', value: feedbackItems.filter(f => f.sentiment === 'neutral').length },
  ];

  const COLORS = ['#3b82f6', '#ef4444', '#6b7280'];

  return (
    <div className="space-y-6">
      {/* Date Range Filter */}
      <DateRangeFilter />

      {/* KPI Cards */}
      <KPICards />

      {/* New Dashboard Components */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TrendChart />
        <TopNegativeTopics />
      </div>

      {/* Original Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment Distribution */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Sentiment Distribution</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {sentimentData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Topic Clusters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Topic Clusters</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={topicClusters}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-600" />
                <XAxis
                  dataKey="name"
                  className="text-gray-600 dark:text-gray-400"
                  fontSize={12}
                />
                <YAxis className="text-gray-600 dark:text-gray-400" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                  }}
                />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Feedback */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
          Recent Feedback ({feedbackItems.length} items)
        </h3>
        <div className="max-h-[400px] overflow-y-auto space-y-3">
          {feedbackItems.slice(0, 20).map((item) => (
            <div
              key={item.id}
              className="p-4 border border-gray-200 dark:border-gray-600 rounded-md bg-gray-50 dark:bg-gray-700"
            >
              <div className={`font-semibold text-sm mb-2 ${
                item.sentiment === 'positive'
                  ? 'text-green-600 dark:text-green-400'
                  : item.sentiment === 'negative'
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-gray-600 dark:text-gray-400'
              }`}>
                {item.sentiment.toUpperCase()} - {item.topic_cluster}
              </div>
              <div className="text-sm text-gray-900 dark:text-gray-100 mb-2">{item.text}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                {new Date(item.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
