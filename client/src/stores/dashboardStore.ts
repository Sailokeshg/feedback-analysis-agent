import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { DateRange, DashboardSummary } from '../types';
import { apiUrl } from '../utils/api';

interface DashboardState {
  dateRange: DateRange;
  dashboardSummary: DashboardSummary | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setDateRange: (dateRange: DateRange) => void;
  fetchDashboardSummary: () => Promise<void>;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

const defaultDateRange: DateRange = {
  start: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000), // 14 days ago
  end: new Date(),
};

export const useDashboardStore = create<DashboardState>()(
  persist(
    (set, get) => ({
      dateRange: defaultDateRange,
      dashboardSummary: null,
      isLoading: false,
      error: null,

      setDateRange: (dateRange) => {
        set({ dateRange });
        // Refetch data when date range changes
        get().fetchDashboardSummary();
      },

      fetchDashboardSummary: async () => {
        set({ isLoading: true, error: null });
        try {
          const { dateRange } = get();
          const startDate = dateRange.start.toISOString().split('T')[0];
          const endDate = dateRange.end.toISOString().split('T')[0];

          const response = await fetch(apiUrl(`api/analytics/dashboard/summary?start_date=${startDate}&end_date=${endDate}`));
          if (!response.ok) {
            throw new Error('Failed to fetch dashboard summary');
          }
          const data = await response.json();
          set({ dashboardSummary: data });
        } catch (error) {
          set({ error: error instanceof Error ? error.message : 'Failed to fetch dashboard summary' });
        } finally {
          set({ isLoading: false });
        }
      },

      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),
    }),
    {
      name: 'dashboard-storage',
      partialize: (state) => ({
        dateRange: state.dateRange,
      }),
    }
  )
);
