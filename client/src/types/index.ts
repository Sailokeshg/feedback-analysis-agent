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

export interface KPIMetrics {
  total_feedback: number;
  negative_percentage: number;
  topics_count: number;
}

export interface DashboardSummary {
  total_feedback: number;
  negative_percentage: number;
  topics_count: number;
  top_negative_topics: Array<{
    name: string;
    count: number;
    negative_percentage: number;
  }>;
  trends_14d: Array<{
    date: string;
    positive: number;
    negative: number;
    neutral: number;
  }>;
}

export interface DateRange {
  start: Date;
  end: Date;
}
