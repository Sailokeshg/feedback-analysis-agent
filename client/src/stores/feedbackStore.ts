import { create } from "zustand";
import {
  FeedbackItem,
  TopicCluster,
  SentimentTrend,
  QueryResult,
} from "../types";
import { apiUrl } from "../utils/api";

interface FeedbackStore {
  feedbackItems: FeedbackItem[];
  topicClusters: TopicCluster[];
  sentimentTrends: SentimentTrend[];
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchFeedback: () => Promise<void>;
  fetchTopics: () => Promise<void>;
  fetchTrends: () => Promise<void>;
  askQuestion: (query: string) => Promise<QueryResult>;
  uploadFeedback: (file: File) => Promise<void>;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useFeedbackStore = create<FeedbackStore>((set, get) => ({
  feedbackItems: [],
  topicClusters: [],
  sentimentTrends: [],
  isLoading: false,
  error: null,

  fetchFeedback: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(apiUrl("api/feedback"), { cache: "no-store" });
      if (!response.ok) {
        set({ error: "Failed to fetch feedback" });
        return;
      }
      const data = await response.json();
      set({ feedbackItems: data.items || [] });
    } catch (error) {
      set({ error: "Failed to fetch feedback" });
    } finally {
      set({ isLoading: false });
    }
  },

  fetchTopics: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(apiUrl("api/topics"), { cache: "no-store" });
      if (!response.ok) {
        set({ error: "Failed to fetch topics" });
        return;
      }
      const data = await response.json();

      // Transform API response to match TopicCluster interface
      const transformedData = data.map((topic: any) => ({
        id: topic.id.toString(),
        name: topic.label,
        count: topic.feedback_count,
        sentiment_distribution: {
          positive: topic.positive_count || 0,
          negative: topic.negative_count || 0,
          neutral: topic.neutral_count || 0,
        }
      }));

      set({ topicClusters: transformedData });
    } catch (error) {
      set({ error: "Failed to fetch topics" });
    } finally {
      set({ isLoading: false });
    }
  },

  fetchTrends: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(apiUrl("api/trends"), { cache: "no-store" });
      if (!response.ok) {
        set({ error: "Failed to fetch trends" });
        return;
      }
      const data = await response.json();
      set({ sentimentTrends: data });
    } catch (error) {
      set({ error: "Failed to fetch trends" });
    } finally {
      set({ isLoading: false });
    }
  },

  askQuestion: async (query: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(apiUrl("api/query"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });
      const data = await response.json();
      return data;
    } catch (error) {
      set({ error: "Failed to process query" });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  uploadFeedback: async (file: File) => {
    set({ isLoading: true, error: null });
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(apiUrl("api/upload"), {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      // Refresh data after upload
      await Promise.all([
        get().fetchFeedback(),
        get().fetchTopics(),
        get().fetchTrends(),
      ]);
    } catch (error) {
      set({ error: "Failed to upload feedback" });
    } finally {
      set({ isLoading: false });
    }
  },

  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
}));
