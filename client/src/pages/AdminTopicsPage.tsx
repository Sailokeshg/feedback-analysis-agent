import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PencilIcon, ArrowPathIcon, CheckIcon, XMarkIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

interface Topic {
  id: number;
  label: string;
  keywords: string[];
  updated_at: string;
}

interface FeedbackItem {
  id: string;
  text: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  sentiment_score: number;
  source: string;
}

interface TopicFeedbackResponse {
  topic_id: number;
  feedback: FeedbackItem[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
    has_next: boolean;
  };
}

const fetchTopics = async (): Promise<Topic[]> => {
  const response = await fetch('/admin/topics');
  if (!response.ok) {
    throw new Error('Failed to fetch topics');
  }
  return response.json();
};

const fetchTopicFeedback = async (topicId: number, page: number = 1): Promise<TopicFeedbackResponse> => {
  const response = await fetch(`/admin/topics/${topicId}/feedback?page=${page}&page_size=10`);
  if (!response.ok) {
    throw new Error('Failed to fetch topic feedback');
  }
  return response.json();
};

const updateTopic = async ({ topicId, label, keywords }: { topicId: number; label: string; keywords: string[] }) => {
  const token = localStorage.getItem('admin_token');
  const response = await fetch('/admin/relabel-topic', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      topic_id: topicId,
      new_label: label,
      new_keywords: keywords,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to update topic');
  }

  return response.json();
};

const reassignFeedback = async ({
  feedbackId,
  newTopicId,
  reason
}: {
  feedbackId: string;
  newTopicId: number;
  reason?: string;
}) => {
  const token = localStorage.getItem('admin_token');
  const response = await fetch('/admin/reassign-feedback', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      feedback_id: feedbackId,
      new_topic_id: newTopicId,
      reason: reason,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to reassign feedback');
  }

  return response.json();
};

const AdminTopicsPage = () => {
  const [editingTopic, setEditingTopic] = useState<number | null>(null);
  const [editLabel, setEditLabel] = useState('');
  const [editKeywords, setEditKeywords] = useState<string[]>([]);
  const [selectedTopic, setSelectedTopic] = useState<number | null>(null);
  const [reassigningFeedback, setReassigningFeedback] = useState<string | null>(null);
  const [reassignReason, setReassignReason] = useState('');

  const queryClient = useQueryClient();

  const { data: topics, isLoading: topicsLoading, error: topicsError } = useQuery({
    queryKey: ['admin-topics'],
    queryFn: fetchTopics,
    staleTime: 30000, // 30 seconds
  });

  const { data: topicFeedback, isLoading: feedbackLoading } = useQuery({
    queryKey: ['topic-feedback', selectedTopic],
    queryFn: () => selectedTopic ? fetchTopicFeedback(selectedTopic) : Promise.resolve(null),
    enabled: !!selectedTopic,
    staleTime: 30000,
  });

  const updateTopicMutation = useMutation({
    mutationFn: updateTopic,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-topics'] });
      setEditingTopic(null);
      setEditLabel('');
      setEditKeywords([]);
    },
  });

  const reassignMutation = useMutation({
    mutationFn: reassignFeedback,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['topic-feedback'] });
      queryClient.invalidateQueries({ queryKey: ['admin-topics'] });
      setReassigningFeedback(null);
      setReassignReason('');
    },
  });

  const startEditing = (topic: Topic) => {
    setEditingTopic(topic.id);
    setEditLabel(topic.label);
    setEditKeywords([...topic.keywords]);
  };

  const cancelEditing = () => {
    setEditingTopic(null);
    setEditLabel('');
    setEditKeywords([]);
  };

  const saveTopic = () => {
    if (editingTopic && editLabel.trim()) {
      updateTopicMutation.mutate({
        topicId: editingTopic,
        label: editLabel.trim(),
        keywords: editKeywords.filter(k => k.trim()).map(k => k.trim()),
      });
    }
  };

  const startReassigning = (feedbackId: string) => {
    setReassigningFeedback(feedbackId);
    setReassignReason('');
  };

  const confirmReassign = (newTopicId: number) => {
    if (reassigningFeedback) {
      reassignMutation.mutate({
        feedbackId: reassigningFeedback,
        newTopicId,
        reason: reassignReason.trim() || undefined,
      });
    }
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

  if (topicsLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Topic Management</h1>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <div className="animate-pulse space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (topicsError) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Topic Management</h1>
        </div>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="text-red-600 dark:text-red-400 text-lg font-semibold mb-2">Error loading topics</div>
            <div className="text-gray-600 dark:text-gray-400">{topicsError.message}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Topic Management</h1>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {topics?.length || 0} topics available
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Topics List */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">Topics</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">Edit labels and keywords</p>
          </div>

          <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-96 overflow-y-auto">
            {topics?.map((topic) => (
              <div key={topic.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                {editingTopic === topic.id ? (
                  <div className="space-y-3">
                    <input
                      type="text"
                      value={editLabel}
                      onChange={(e) => setEditLabel(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100"
                      placeholder="Topic label"
                    />
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Keywords:</label>
                      <textarea
                        value={editKeywords.join(', ')}
                        onChange={(e) => setEditKeywords(e.target.value.split(',').map(k => k.trim()).filter(k => k))}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100"
                        placeholder="keyword1, keyword2, keyword3"
                        rows={2}
                      />
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={saveTopic}
                        disabled={updateTopicMutation.isPending}
                        className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                      >
                        <CheckIcon className="h-4 w-4 mr-1" />
                        Save
                      </button>
                      <button
                        onClick={cancelEditing}
                        className="inline-flex items-center px-3 py-1 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
                      >
                        <XMarkIcon className="h-4 w-4 mr-1" />
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">{topic.label}</h3>
                        <button
                          onClick={() => setSelectedTopic(selectedTopic === topic.id ? null : topic.id)}
                          className="inline-flex items-center px-2 py-1 border border-gray-300 dark:border-gray-600 text-xs font-medium rounded text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
                        >
                          <DocumentTextIcon className="h-3 w-3 mr-1" />
                          {selectedTopic === topic.id ? 'Hide' : 'View'} Feedback
                        </button>
                      </div>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {topic.keywords.slice(0, 3).map((keyword, idx) => (
                          <span key={idx} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-300">
                            {keyword}
                          </span>
                        ))}
                        {topic.keywords.length > 3 && (
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            +{topic.keywords.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => startEditing(topic)}
                      className="ml-4 inline-flex items-center px-3 py-1 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
                    >
                      <PencilIcon className="h-4 w-4 mr-1" />
                      Edit
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Topic Feedback */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-gray-100">
              {selectedTopic ? `Topic ${selectedTopic} Feedback` : 'Select a topic to view feedback'}
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Reassign misclassified feedback comments
            </p>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {selectedTopic ? (
              feedbackLoading ? (
                <div className="p-6">
                  <div className="animate-pulse space-y-3">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
                    ))}
                  </div>
                </div>
              ) : topicFeedback?.feedback?.length ? (
                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                  {topicFeedback.feedback.map((feedback) => (
                    <div key={feedback.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                      {reassigningFeedback === feedback.id ? (
                        <div className="space-y-3">
                          <div className="text-sm text-gray-900 dark:text-gray-100 font-medium">
                            Reassign this feedback to:
                          </div>
                          <select
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100"
                            onChange={(e) => {
                              const newTopicId = parseInt(e.target.value);
                              if (newTopicId && newTopicId !== selectedTopic) {
                                confirmReassign(newTopicId);
                              }
                            }}
                          >
                            <option value="">Select new topic...</option>
                            {topics?.filter(t => t.id !== selectedTopic).map((topic) => (
                              <option key={topic.id} value={topic.id}>
                                {topic.label}
                              </option>
                            ))}
                          </select>
                          <input
                            type="text"
                            value={reassignReason}
                            onChange={(e) => setReassignReason(e.target.value)}
                            placeholder="Reason for reassignment (optional)"
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100"
                          />
                          <div className="flex space-x-2">
                            <button
                              onClick={() => setReassigningFeedback(null)}
                              className="inline-flex items-center px-3 py-1 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
                            >
                              <XMarkIcon className="h-4 w-4 mr-1" />
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-2">
                          <div className="flex items-start justify-between">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getSentimentColor(feedback.sentiment)}`}>
                              {feedback.sentiment.toUpperCase()}
                            </span>
                            <button
                              onClick={() => startReassigning(feedback.id)}
                              className="inline-flex items-center px-2 py-1 border border-gray-300 dark:border-gray-600 text-xs font-medium rounded text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700"
                            >
                              <ArrowPathIcon className="h-3 w-3 mr-1" />
                              Reassign
                            </button>
                          </div>
                          <div className="text-sm text-gray-900 dark:text-gray-100">
                            {feedback.text}
                          </div>
                          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                            <span>Source: {feedback.source}</span>
                            <span>Score: {feedback.sentiment_score.toFixed(2)}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-6 text-center">
                  <div className="text-gray-500 dark:text-gray-400">No feedback found for this topic</div>
                </div>
              )
            ) : (
              <div className="p-6 text-center">
                <div className="text-gray-500 dark:text-gray-400">
                  Click "View Feedback" on a topic to see and reassign feedback comments
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Status Messages */}
      {updateTopicMutation.isSuccess && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md p-4">
          <div className="text-green-800 dark:text-green-300">Topic updated successfully!</div>
        </div>
      )}

      {updateTopicMutation.isError && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
          <div className="text-red-800 dark:text-red-300">
            Failed to update topic: {updateTopicMutation.error?.message}
          </div>
        </div>
      )}

      {reassignMutation.isSuccess && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md p-4">
          <div className="text-green-800 dark:text-green-300">Feedback reassigned successfully!</div>
        </div>
      )}

      {reassignMutation.isError && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4">
          <div className="text-red-800 dark:text-red-300">
            Failed to reassign feedback: {reassignMutation.error?.message}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminTopicsPage;
