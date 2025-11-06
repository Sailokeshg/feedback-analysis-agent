export interface FeedbackItem {
  id: string;
  text: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  sentiment_score: number;
  topic_cluster: string;
  created_at: string;
  source: string;
}

export interface TopicCluster {
  id: string;
  name: string;
  count: number;
  sentiment_distribution: {
    positive: number;
    negative: number;
    neutral: number;
  };
}

export interface SentimentTrend {
  date: string;
  positive: number;
  negative: number;
  neutral: number;
}

export interface QueryResult {
  query: string;
  answer: string;
  sources: FeedbackItem[];
}
