import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { apiUrl } from '../utils/api';

interface FeedbackExample {
  id: string;
  text: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  sentiment_score: number;
  created_at: string;
  source: string;
}

interface TopicExamplesResponse {
  items: FeedbackExample[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

const fetchTopicExamples = async (
  topicId: string,
  page: number = 1,
  pageSize: number = 20
): Promise<TopicExamplesResponse> => {
  const response = await fetch(
    apiUrl(`api/analytics/examples?topic=${topicId}&page=${page}&page_size=${pageSize}`)
  );
  if (!response.ok) {
    throw new Error('Failed to fetch topic examples');
  }
  return response.json();
};

const TopicDetail = () => {
  const { topicId } = useParams<{ topicId: string }>();
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading, error } = useQuery<TopicExamplesResponse>({
    queryKey: ['topic-examples', topicId, currentPage],
    queryFn: () => fetchTopicExamples(topicId!, currentPage, pageSize),
    enabled: !!topicId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

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

  if (!topicId) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="text-red-600 dark:text-red-400 text-lg font-semibold mb-2">Topic not found</div>
          <Link to="/topics" className="text-blue-600 dark:text-blue-400 hover:underline">
            ← Back to Topics
          </Link>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Link to="/topics" className="flex items-center text-blue-600 dark:text-blue-400 hover:underline">
            <ChevronLeftIcon className="h-4 w-4 mr-1" />
            Back to Topics
          </Link>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-6"></div>
            {[...Array(5)].map((_, i) => (
              <div key={i} className="mb-4">
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-2"></div>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
              </div>
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
          <Link to="/topics" className="flex items-center text-blue-600 dark:text-blue-400 hover:underline">
            <ChevronLeftIcon className="h-4 w-4 mr-1" />
            Back to Topics
          </Link>
        </div>

        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="text-red-600 dark:text-red-400 text-lg font-semibold mb-2">Error loading topic examples</div>
            <div className="text-gray-600 dark:text-gray-400 mb-4">{error.message}</div>
            <Link to="/topics" className="text-blue-600 dark:text-blue-400 hover:underline">
              ← Back to Topics
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const examples = data?.items || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link to="/topics" className="flex items-center text-blue-600 dark:text-blue-400 hover:underline">
          <ChevronLeftIcon className="h-4 w-4 mr-1" />
          Back to Topics
        </Link>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {total} examples found
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
          Topic Examples
        </h1>

        {examples.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-500 dark:text-gray-400">No examples found for this topic</div>
          </div>
        ) : (
          <>
            <div className="space-y-4 mb-6">
              {examples.map((example) => (
                <div
                  key={example.id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                >
                  <div className="flex items-start justify-between mb-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSentimentColor(example.sentiment)}`}>
                      {example.sentiment.toUpperCase()}
                    </span>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {new Date(example.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="text-sm text-gray-900 dark:text-gray-100 mb-2">
                    {example.text}
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                    <span>Source: {example.source}</span>
                    <span>Sentiment Score: {example.sentiment_score.toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-700 dark:text-gray-300">
                  Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, total)} of {total} results
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

                  <div className="flex items-center space-x-1">
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      const pageNumber = i + 1;
                      const isActive = pageNumber === currentPage;
                      return (
                        <button
                          key={pageNumber}
                          onClick={() => setCurrentPage(pageNumber)}
                          className={`px-3 py-1 border rounded-md text-sm font-medium ${
                            isActive
                              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400'
                              : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                          }`}
                        >
                          {pageNumber}
                        </button>
                      );
                    })}
                  </div>

                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="inline-flex items-center px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                    <ChevronRightIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default TopicDetail;
