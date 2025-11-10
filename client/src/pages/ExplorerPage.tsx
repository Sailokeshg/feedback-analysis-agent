import { useState, useMemo, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { apiUrl } from '../utils/api';
import { ChevronLeftIcon, ChevronRightIcon, FunnelIcon } from '@heroicons/react/24/outline';

interface FeedbackItem {
  id: string;
  text: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  sentiment_score: number;
  topic_cluster: string;
  created_at: string;
  source: string;
}

interface ExplorerFilters {
  startDate: string;
  endDate: string;
  sentiment: string;
  topic: string;
  search: string;
}

interface ExplorerResponse {
  items: FeedbackItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

const fetchExplorerResults = async (filters: ExplorerFilters, page: number = 1): Promise<ExplorerResponse> => {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: '20',
  });

  if (filters.startDate) params.set('start_date', filters.startDate);
  if (filters.endDate) params.set('end_date', filters.endDate);
  if (filters.sentiment && filters.sentiment !== 'all') params.set('sentiment', filters.sentiment);
  if (filters.topic) params.set('topic', filters.topic);
  if (filters.search) params.set('search', filters.search);

  const response = await fetch(apiUrl(`api/feedback?${params.toString()}`));
  if (!response.ok) {
    throw new Error('Failed to fetch explorer results');
  }
  return response.json();
};

const fetchTopicsList = async (): Promise<string[]> => {
  const response = await fetch(apiUrl('analytics/topics'));
  if (!response.ok) {
    throw new Error('Failed to fetch topics');
  }
  const data = await response.json();
  return data.map((topic: any) => topic.label);
};

const ExplorerPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [currentPage, setCurrentPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);

  const [filters, setFilters] = useState<ExplorerFilters>({
    startDate: searchParams.get('startDate') || '',
    endDate: searchParams.get('endDate') || '',
    sentiment: searchParams.get('sentiment') || 'all',
    topic: searchParams.get('topic') || '',
    search: searchParams.get('search') || '',
  });

  // Sync URL params with filters
  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.startDate) params.set('startDate', filters.startDate);
    if (filters.endDate) params.set('endDate', filters.endDate);
    if (filters.sentiment && filters.sentiment !== 'all') params.set('sentiment', filters.sentiment);
    if (filters.topic) params.set('topic', filters.topic);
    if (filters.search) params.set('search', filters.search);

    setSearchParams(params, { replace: true });
  }, [filters, setSearchParams]);

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [filters]);

  const { data: results, isLoading, error } = useQuery<ExplorerResponse>({
    queryKey: ['explorer', filters, currentPage],
    queryFn: () => fetchExplorerResults(filters, currentPage),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
  });

  const { data: topics } = useQuery({
    queryKey: ['topics-list'],
    queryFn: fetchTopicsList,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });

  const updateFilter = (key: keyof ExplorerFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      startDate: '',
      endDate: '',
      sentiment: 'all',
      topic: '',
      search: '',
    });
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20';
      case 'negative':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20';
      default:
        return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  const hasActiveFilters = Object.values(filters).some(value => value && value !== 'all');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Feedback Explorer</h1>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          <FunnelIcon className="h-4 w-4 mr-2" />
          Filters {hasActiveFilters && '•'}
        </button>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
            <div>
              <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Start Date
              </label>
              <input
                id="startDate"
                type="date"
                value={filters.startDate}
                onChange={(e) => updateFilter('startDate', e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100 sm:text-sm"
              />
            </div>

            <div>
              <label htmlFor="endDate" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                End Date
              </label>
              <input
                id="endDate"
                type="date"
                value={filters.endDate}
                onChange={(e) => updateFilter('endDate', e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100 sm:text-sm"
              />
            </div>

            <div>
              <label htmlFor="sentiment" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Sentiment
              </label>
              <select
                id="sentiment"
                value={filters.sentiment}
                onChange={(e) => updateFilter('sentiment', e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100 sm:text-sm"
              >
                <option value="all">All Sentiments</option>
                <option value="positive">Positive</option>
                <option value="negative">Negative</option>
                <option value="neutral">Neutral</option>
              </select>
            </div>

            <div>
              <label htmlFor="topic" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Topic
              </label>
              <select
                id="topic"
                value={filters.topic}
                onChange={(e) => updateFilter('topic', e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100 sm:text-sm"
              >
                <option value="">All Topics</option>
                {topics?.map((topic) => (
                  <option key={topic} value={topic}>{topic}</option>
                ))}
              </select>
            </div>

            <div className="md:col-span-2">
              <label htmlFor="search" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Search Text
              </label>
              <input
                id="search"
                type="text"
                placeholder="Search in feedback text..."
                value={filters.search}
                onChange={(e) => updateFilter('search', e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100 sm:text-sm"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={clearFilters}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
            >
              Clear Filters
            </button>
          </div>
        </div>
      )}

      {/* Results */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        {isLoading ? (
          <div className="animate-pulse p-6">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="mb-4">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="p-6 text-center">
            <div className="text-red-600 dark:text-red-400 text-lg font-semibold mb-2">Error loading results</div>
            <div className="text-gray-600 dark:text-gray-400">{error.message}</div>
          </div>
        ) : (
          <>
            <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                {results?.total || 0} results found
              </div>
            </div>

            {results?.items.length === 0 ? (
              <div className="p-6 text-center">
                <div className="text-gray-500 dark:text-gray-400">No results found matching your filters</div>
              </div>
            ) : (
              <>
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {results?.items.map((item) => (
                    <div key={item.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      <div className="flex items-start justify-between mb-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSentimentColor(item.sentiment)}`}>
                          {item.sentiment.toUpperCase()}
                        </span>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(item.created_at).toLocaleDateString()} • {item.source}
                        </div>
                      </div>
                      <div className="text-sm text-gray-900 dark:text-gray-100 mb-2">
                        {item.text}
                      </div>
                      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                        <span>Topic: {item.topic_cluster}</span>
                        <span>Score: {item.sentiment_score.toFixed(2)}</span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pagination */}
                {results && results.total > 20 && (
                  <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-gray-700 dark:text-gray-300">
                        Showing {((currentPage - 1) * 20) + 1} to {Math.min(currentPage * 20, results.total)} of {results.total} results
                      </div>

                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                          disabled={currentPage === 1}
                          className="inline-flex items-center px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <ChevronLeftIcon className="h-4 w-4" />
                          Previous
                        </button>

                        <button
                          onClick={() => setCurrentPage(currentPage + 1)}
                          disabled={!results.has_next}
                          className="inline-flex items-center px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Next
                          <ChevronRightIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ExplorerPage;
