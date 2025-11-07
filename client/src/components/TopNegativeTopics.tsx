import { useDashboardStore } from '../stores/dashboardStore';

const TopicItemSkeleton = () => (
  <div className="animate-pulse">
    <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 last:border-b-0">
      <div className="flex-1">
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-1"></div>
        <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
      </div>
      <div className="text-right">
        <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-16 mb-1"></div>
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-12"></div>
      </div>
    </div>
  </div>
);

const TopNegativeTopics = () => {
  const { dashboardSummary, isLoading } = useDashboardStore();

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <div className="animate-pulse mb-4">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
        </div>
        <div className="space-y-0">
          {[...Array(5)].map((_, i) => (
            <TopicItemSkeleton key={i} />
          ))}
        </div>
      </div>
    );
  }

  const topics = dashboardSummary?.top_negative_topics || [];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">Top Negative Topics</h3>

      {topics.length === 0 ? (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          No negative topics found
        </div>
      ) : (
        <div className="space-y-0">
          {topics.slice(0, 10).map((topic, index) => (
            <div
              key={topic.name}
              className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 last:border-b-0 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    #{index + 1}
                  </span>
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {topic.name}
                  </span>
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {topic.count} total mentions
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold text-red-600 dark:text-red-400">
                  {topic.negative_percentage.toFixed(1)}%
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  negative
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TopNegativeTopics;
