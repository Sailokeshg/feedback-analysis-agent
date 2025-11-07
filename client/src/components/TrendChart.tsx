import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useDashboardStore } from '../stores/dashboardStore';

const TrendChartSkeleton = () => (
  <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
    <div className="animate-pulse">
      <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4"></div>
      <div className="h-[300px] bg-gray-200 dark:bg-gray-700 rounded"></div>
    </div>
  </div>
);

const TrendChart = () => {
  const { dashboardSummary, isLoading } = useDashboardStore();

  if (isLoading) {
    return <TrendChartSkeleton />;
  }

  if (!dashboardSummary?.trends_14d || dashboardSummary.trends_14d.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">14-Day Trend</h3>
        <div className="h-[300px] flex items-center justify-center text-gray-500 dark:text-gray-400">
          No trend data available
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">14-Day Trend</h3>
      <div className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={dashboardSummary.trends_14d}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-600" />
            <XAxis
              dataKey="date"
              className="text-gray-600 dark:text-gray-400"
              fontSize={12}
              tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
            />
            <YAxis className="text-gray-600 dark:text-gray-400" fontSize={12} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
              }}
              labelFormatter={(value) => new Date(value).toLocaleDateString()}
            />
            <Line
              type="monotone"
              dataKey="positive"
              stroke="#10b981"
              strokeWidth={2}
              name="Positive"
            />
            <Line
              type="monotone"
              dataKey="negative"
              stroke="#ef4444"
              strokeWidth={2}
              name="Negative"
            />
            <Line
              type="monotone"
              dataKey="neutral"
              stroke="#6b7280"
              strokeWidth={2}
              name="Neutral"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default TrendChart;
