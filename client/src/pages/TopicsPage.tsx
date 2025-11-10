import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiUrl } from '../utils/api';
import { ChevronUpIcon, ChevronDownIcon, ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/outline';

interface TopicAnalytics {
  topic_id: number;
  label: string;
  count: number | null;
  avg_sentiment: number | string | null;
  delta_week: number | string | null;
}

const fetchTopicsAnalytics = async (): Promise<TopicAnalytics[]> => {
  const response = await fetch(apiUrl('analytics/topics'));
  if (!response.ok) {
    throw new Error('Failed to fetch topics analytics');
  }
  return response.json();
};

const TopicsPage = () => {
  const [sortField, setSortField] = useState<keyof TopicAnalytics>('count');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  const { data: topics, isLoading, error } = useQuery({
    queryKey: ['topics-analytics'],
    queryFn: fetchTopicsAnalytics,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  const sortedTopics = useMemo(() => {
    if (!topics) return [];
    return [...topics].sort((a, b) => {
      let aValue = a[sortField];
      let bValue = b[sortField];

      // Convert numeric fields to numbers for proper comparison
      if (sortField === 'count' || sortField === 'avg_sentiment' || sortField === 'delta_week') {
        aValue = Number(aValue) || 0;
        bValue = Number(bValue) || 0;
      }

      const direction = sortDirection === 'asc' ? 1 : -1;
      return (aValue < bValue ? -1 : aValue > bValue ? 1 : 0) * direction;
    });
  }, [topics, sortField, sortDirection]);

  const handleSort = (field: keyof TopicAnalytics) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const getSentimentColor = (sentiment: number) => {
    if (sentiment > 0.1) return 'text-green-600 dark:text-green-400';
    if (sentiment < -0.1) return 'text-red-600 dark:text-red-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  const getDeltaColor = (delta: number) => {
    if (delta > 5) return 'text-green-600 dark:text-green-400';
    if (delta < -5) return 'text-red-600 dark:text-red-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Topics</h1>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="animate-pulse">
            <div className="h-16 bg-gray-200 dark:bg-gray-700 rounded-t-lg"></div>
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 last:border-b-0"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Topics</h1>
        </div>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="text-red-600 dark:text-red-400 text-lg font-semibold mb-2">Error loading topics</div>
            <div className="text-gray-600 dark:text-gray-400">{error.message}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Topics</h1>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {topics?.length || 0} topics found
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                  onClick={() => handleSort('label')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Topic Label</span>
                    {sortField === 'label' && (
                      sortDirection === 'asc' ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />
                    )}
                  </div>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                  onClick={() => handleSort('count')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Volume</span>
                    {sortField === 'count' && (
                      sortDirection === 'asc' ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />
                    )}
                  </div>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                  onClick={() => handleSort('avg_sentiment')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Avg Sentiment</span>
                    {sortField === 'avg_sentiment' && (
                      sortDirection === 'asc' ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />
                    )}
                  </div>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                  onClick={() => handleSort('delta_week')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Week-over-Week</span>
                    {sortField === 'delta_week' && (
                      sortDirection === 'asc' ? <ChevronUpIcon className="h-4 w-4" /> : <ChevronDownIcon className="h-4 w-4" />
                    )}
                  </div>
                </th>
                <th scope="col" className="relative px-6 py-3">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {sortedTopics.map((topic) => (
                <tr key={topic.topic_id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {topic.label}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 dark:text-gray-100">
                      {topic.count?.toLocaleString() || 0}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-sm font-medium ${getSentimentColor(Number(topic.avg_sentiment) || 0)}`}>
                      {Number(topic.avg_sentiment || 0).toFixed(2)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`flex items-center text-sm font-medium ${getDeltaColor(Number(topic.delta_week) || 0)}`}>
                      {Number(topic.delta_week) > 0 && <ArrowUpIcon className="h-4 w-4 mr-1" />}
                      {Number(topic.delta_week) < 0 && <ArrowDownIcon className="h-4 w-4 mr-1" />}
                      {Number(topic.delta_week) > 0 ? '+' : ''}{Number(topic.delta_week || 0).toFixed(1)}%
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Link
                      to={`/topics/${topic.topic_id}`}
                      className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300"
                    >
                      View Details →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TopicsPage;
