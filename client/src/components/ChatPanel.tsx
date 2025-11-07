import { useState, useRef, useEffect } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  ChatBubbleLeftRightIcon,
  XMarkIcon,
  PaperAirplaneIcon,
  ClipboardDocumentIcon,
  BoltIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

interface Citation {
  feedback_id: string;
  topic_id?: number;
}

interface ChatResponse {
  answer: string;
  citations: Citation[];
}

interface FeedbackSnippet {
  id: string;
  text: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  created_at: string;
  topic_cluster: string;
}

interface ChatMessage {
  id: string;
  question: string;
  answer?: string;
  citations?: Citation[];
  isLoading: boolean;
  error?: string;
  timestamp: Date;
  streamingText?: string; // For streaming effect
}

const quickTemplates = [
  "Top pain points this week",
  "Most positive feedback trends",
  "Sentiment analysis summary",
  "Common customer complaints",
  "Recent feedback highlights",
  "Topic distribution overview",
  "Weekly summary report",
  "Customer satisfaction trends"
];

// Citation Tooltip Component
const CitationTooltip = ({
  citation,
  snippet,
  children
}: {
  citation: Citation;
  snippet?: FeedbackSnippet;
  children: React.ReactNode;
}) => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <span className="relative inline-block">
      <button
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className="inline-flex items-center px-1 py-0.5 mx-0.5 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded border hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
      >
        <DocumentTextIcon className="h-3 w-3 mr-0.5" />
        {children}
      </button>

      {isVisible && (
        <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 z-50">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3 max-w-xs">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Feedback Snippet</div>
            {snippet ? (
              <>
                <div className="text-sm text-gray-900 dark:text-gray-100 mb-2 line-clamp-3">
                  {snippet.text}
                </div>
                <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                  <span>{snippet.sentiment}</span>
                  <span>{new Date(snippet.created_at).toLocaleDateString()}</span>
                </div>
              </>
            ) : (
              <div className="text-sm text-gray-500 dark:text-gray-400">Loading...</div>
            )}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-200 dark:border-t-gray-700"></div>
          </div>
        </div>
      )}
    </span>
  );
};

// Function to parse answer text and replace citations with components
const renderAnswerWithCitations = (
  answer: string,
  citations: Citation[],
  feedbackSnippets: Record<string, FeedbackSnippet>
) => {
  if (!citations || citations.length === 0) {
    return <div className="whitespace-pre-wrap">{answer}</div>;
  }

  // Create a map of citation indices for easy lookup
  const citationMap = new Map<string, Citation>();
  citations.forEach((citation, index) => {
    citationMap.set(citation.feedback_id, citation);
  });

  // Simple regex to find feedback_id patterns in the text
  const parts: (string | { type: 'citation'; citation: Citation; index: number })[] = [];
  let lastIndex = 0;

  // Look for patterns like "feedback_id: uuid" or just uuids
  const feedbackIdRegex = /\b([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b/gi;

  let match;
  while ((match = feedbackIdRegex.exec(answer)) !== null) {
    const feedbackId = match[1];

    // Add text before the match
    if (match.index > lastIndex) {
      parts.push(answer.slice(lastIndex, match.index));
    }

    // Add citation if it exists
    const citation = citationMap.get(feedbackId);
    if (citation) {
      parts.push({
        type: 'citation' as const,
        citation,
        index: citations.findIndex(c => c.feedback_id === feedbackId) + 1
      });
    } else {
      // If no citation found, just add the text
      parts.push(match[0]);
    }

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < answer.length) {
    parts.push(answer.slice(lastIndex));
  }

  return (
    <div className="whitespace-pre-wrap">
      {parts.map((part, index) => {
        if (typeof part === 'string') {
          return <span key={index}>{part}</span>;
        } else {
          return (
            <CitationTooltip
              key={index}
              citation={part.citation}
              snippet={feedbackSnippets[part.citation.feedback_id]}
            >
              [{part.index}]
            </CitationTooltip>
          );
        }
      })}
    </div>
  );
};

// Custom hook for streaming text effect
const useStreamingText = (fullText: string, isActive: boolean, speed: number = 30) => {
  const [displayText, setDisplayText] = useState('');

  useEffect(() => {
    if (!isActive || !fullText) {
      setDisplayText(fullText);
      return;
    }

    setDisplayText('');
    let currentIndex = 0;

    const interval = setInterval(() => {
      if (currentIndex < fullText.length) {
        setDisplayText(fullText.slice(0, currentIndex + 1));
        currentIndex++;
      } else {
        clearInterval(interval);
      }
    }, speed);

    return () => clearInterval(interval);
  }, [fullText, isActive, speed]);

  return displayText;
};

const ChatPanel = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [feedbackSnippets, setFeedbackSnippets] = useState<Record<string, FeedbackSnippet>>({});
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle streaming text effect
  useEffect(() => {
    if (!streamingMessageId) return;

    const message = messages.find(m => m.id === streamingMessageId);
    if (!message || !message.answer) return;

    let currentIndex = message.streamingText?.length || 0;
    const fullText = message.answer;

    if (currentIndex >= fullText.length) {
      setStreamingMessageId(null);
      return;
    }

    const interval = setInterval(() => {
      if (currentIndex < fullText.length) {
        const newText = fullText.slice(0, currentIndex + 1);
        setMessages(prev => prev.map(msg =>
          msg.id === streamingMessageId
            ? { ...msg, streamingText: newText }
            : msg
        ));
        currentIndex++;
      } else {
        clearInterval(interval);
        setStreamingMessageId(null);
      }
    }, 20); // Speed of streaming

    return () => clearInterval(interval);
  }, [streamingMessageId, messages]);

  // Fetch feedback snippet for a citation
  const fetchFeedbackSnippet = async (feedbackId: string): Promise<FeedbackSnippet> => {
    const response = await fetch(`/api/feedback/${feedbackId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch feedback snippet');
    }
    return response.json();
  };

  const citationQuery = useQuery({
    queryKey: ['citation-snippet'],
    queryFn: () => Promise.resolve({}),
    enabled: false,
  });

  // Chat mutation
  const chatMutation = useMutation({
    mutationFn: async (question: string): Promise<ChatResponse> => {
      const response = await fetch('/api/chat/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      return response.json();
    },
    onMutate: (question) => {
      const messageId = Date.now().toString();
      const newMessage: ChatMessage = {
        id: messageId,
        question,
        isLoading: true,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, newMessage]);
      setCurrentQuestion('');
      return { messageId };
    },
    onSuccess: (data, question, context) => {
      const messageId = context?.messageId;
      if (messageId) {
        setStreamingMessageId(messageId);
        setMessages(prev => prev.map(msg =>
          msg.id === messageId
            ? {
                ...msg,
                answer: data.answer,
                citations: data.citations,
                streamingText: '', // Start with empty text for streaming
                isLoading: false,
              }
            : msg
        ));

        // Pre-fetch citation snippets
        data.citations?.forEach(citation => {
          fetchFeedbackSnippet(citation.feedback_id).then(snippet => {
            setFeedbackSnippets(prev => ({ ...prev, [citation.feedback_id]: snippet }));
          }).catch(error => {
            console.warn('Failed to fetch citation snippet:', error);
          });
        });

        // Stop streaming after a delay (simulate completion)
        setTimeout(() => {
          setStreamingMessageId(null);
        }, data.answer.length * 30 + 500); // Speed + buffer
      }
    },
    onError: (error, question, context) => {
      setMessages(prev => prev.map(msg =>
        msg.id === context?.messageId
          ? {
              ...msg,
              error: error.message,
              isLoading: false,
            }
          : msg
      ));
    },
  });

  const handleSubmit = (question: string) => {
    if (!question.trim()) return;
    chatMutation.mutate(question);
  };

  const handleTemplateClick = (template: string) => {
    handleSubmit(template);
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // Could add a toast notification here
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const renderMessage = (message: ChatMessage) => {
    // Use streaming text if this message is currently streaming
    const isStreaming = streamingMessageId === message.id;
    const displayText = isStreaming ? message.streamingText || '' : message.answer || '';

    return (
      <div key={message.id} className="space-y-3">
        {/* User Question */}
        <div className="flex justify-end">
          <div className="bg-blue-600 text-white rounded-lg px-4 py-2 max-w-md">
            {message.question}
          </div>
        </div>

        {/* Assistant Answer */}
        <div className="flex justify-start">
          <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-3 max-w-2xl">
            {message.isLoading ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-gray-600 dark:text-gray-400">Thinking...</span>
              </div>
            ) : message.error ? (
              <div className="flex items-start space-x-2 text-red-600 dark:text-red-400">
                <ExclamationTriangleIcon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="font-medium">Error</div>
                  <div className="text-sm text-red-500 dark:text-red-300">{message.error}</div>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="text-gray-900 dark:text-gray-100">
                  {isStreaming ? (
                    <div className="whitespace-pre-wrap">{displayText}</div>
                  ) : (
                    renderAnswerWithCitations(displayText, message.citations!, feedbackSnippets)
                  )}
                  {isStreaming && <span className="inline-block w-2 h-4 bg-blue-600 ml-1 animate-pulse"></span>}
                </div>

                {!isStreaming && message.citations && message.citations.length > 0 && (
                  <div className="flex items-center justify-between pt-2 border-t border-gray-200 dark:border-gray-700">
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {message.citations.length} citation{message.citations.length !== 1 ? 's' : ''}
                    </div>
                    <button
                      onClick={() => copyToClipboard(message.answer || '')}
                      className="inline-flex items-center px-2 py-1 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      <ClipboardDocumentIcon className="h-3 w-3 mr-1" />
                      Copy
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Chat Toggle Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 bg-blue-600 hover:bg-blue-700 text-white rounded-full p-3 shadow-lg transition-colors z-40"
        aria-label="Open chat"
      >
        <ChatBubbleLeftRightIcon className="h-6 w-6" />
      </button>

      {/* Chat Panel */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black bg-opacity-50"
            onClick={() => setIsOpen(false)}
          />

          {/* Panel */}
          <div className="relative ml-auto w-full max-w-md h-full bg-white dark:bg-gray-900 shadow-xl flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">AI Assistant</h2>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 && (
                <div className="text-center text-gray-500 dark:text-gray-400 py-8">
                  <ChatBubbleLeftRightIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="mb-4">Ask me anything about your customer feedback!</p>

                  {/* Quick Templates */}
                  <div className="space-y-2">
                    <p className="text-sm font-medium">Quick asks:</p>
                    <div className="grid grid-cols-1 gap-2 max-w-xs mx-auto">
                      {quickTemplates.slice(0, 4).map((template, index) => (
                        <button
                          key={index}
                          onClick={() => handleTemplateClick(template)}
                          disabled={chatMutation.isPending}
                          className="text-left text-xs p-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <BoltIcon className="h-3 w-3 inline mr-1" />
                          {template}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {messages.map(renderMessage)}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSubmit(currentQuestion);
                }}
                className="flex space-x-2"
              >
                <input
                  type="text"
                  value={currentQuestion}
                  onChange={(e) => setCurrentQuestion(e.target.value)}
                  placeholder="Ask about customer feedback..."
                  disabled={chatMutation.isPending}
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-gray-100 disabled:opacity-50"
                />
                <button
                  type="submit"
                  disabled={!currentQuestion.trim() || chatMutation.isPending}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white px-4 py-2 rounded-md transition-colors"
                >
                  <PaperAirplaneIcon className="h-4 w-4" />
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatPanel;
