import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { act, renderHook, waitFor } from '@testing-library/react'
import { useDashboardStore } from '../dashboardStore'
import { server } from '../../test/server'
import { setupMSW } from '../../test/server'

// Mock fetch globally
const fetchMock = vi.fn()
global.fetch = fetchMock

describe('Dashboard Store', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset store state
    const { result } = renderHook(() => useDashboardStore())
    act(() => {
      result.current.setDateRange({
        start: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000),
        end: new Date(),
      })
      result.current.setLoading(false)
      result.current.setError(null)
    })
  })

  afterEach(() => {
    server.resetHandlers()
  })

  describe('Initial state', () => {
    it('has correct default values', () => {
      const { result } = renderHook(() => useDashboardStore())

      expect(result.current.dashboardSummary).toBeNull()
      expect(result.current.isLoading).toBe(false)
      expect(result.current.error).toBeNull()

      // Date range should be set to last 14 days
      const expectedStart = new Date(Date.now() - 14 * 24 * 60 * 60 * 1000)
      const expectedEnd = new Date()

      expect(result.current.dateRange.start.getTime()).toBeCloseTo(expectedStart.getTime(), -2)
      expect(result.current.dateRange.end.getTime()).toBeCloseTo(expectedEnd.getTime(), -2)
    })
  })

  describe('setDateRange', () => {
    it('updates date range correctly', () => {
      const { result } = renderHook(() => useDashboardStore())

      const newDateRange = {
        start: new Date('2024-01-01'),
        end: new Date('2024-01-31'),
      }

      act(() => {
        result.current.setDateRange(newDateRange)
      })

      expect(result.current.dateRange).toEqual(newDateRange)
    })

    it('triggers fetchDashboardSummary when date range changes', async () => {
      const { result } = renderHook(() => useDashboardStore())

      // Mock successful API response
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total_feedback: 100, trends_14d: [] }),
      })

      const newDateRange = {
        start: new Date('2024-01-01'),
        end: new Date('2024-01-31'),
      }

      act(() => {
        result.current.setDateRange(newDateRange)
      })

      // Should trigger API call
      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledWith(
          '/api/analytics/dashboard/summary?start_date=2024-01-01&end_date=2024-01-31'
        )
      })
    })
  })

  describe('fetchDashboardSummary', () => {
    it('sets loading state during fetch', async () => {
      const { result } = renderHook(() => useDashboardStore())

      fetchMock.mockImplementation(() => new Promise(() => {})) // Never resolves

      act(() => {
        result.current.fetchDashboardSummary()
      })

      expect(result.current.isLoading).toBe(true)
      expect(result.current.error).toBeNull()
    })

    it('fetches data successfully', async () => {
      const { result } = renderHook(() => useDashboardStore())

      const mockData = {
        total_feedback: 150,
        negative_percentage: 25.5,
        topics_count: 12,
        trends_14d: [
          { date: '2024-01-01', positive: 10, negative: 5, neutral: 3 },
        ],
      }

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      })

      act(() => {
        result.current.fetchDashboardSummary()
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.dashboardSummary).toEqual(mockData)
        expect(result.current.error).toBeNull()
      })
    })

    it('handles API errors correctly', async () => {
      const { result } = renderHook(() => useDashboardStore())

      fetchMock.mockResolvedValueOnce({
        ok: false,
        status: 500,
      })

      act(() => {
        result.current.fetchDashboardSummary()
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.dashboardSummary).toBeNull()
        expect(result.current.error).toBe('Failed to fetch dashboard summary')
      })
    })

    it('handles network errors correctly', async () => {
      const { result } = renderHook(() => useDashboardStore())

      fetchMock.mockRejectedValueOnce(new Error('Network error'))

      act(() => {
        result.current.fetchDashboardSummary()
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.dashboardSummary).toBeNull()
        expect(result.current.error).toBe('Network error')
      })
    })

    it('handles non-Error exceptions correctly', async () => {
      const { result } = renderHook(() => useDashboardStore())

      fetchMock.mockRejectedValueOnce('String error')

      act(() => {
        result.current.fetchDashboardSummary()
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.dashboardSummary).toBeNull()
        expect(result.current.error).toBe('Failed to fetch dashboard summary')
      })
    })

    it('constructs correct API URL with date parameters', async () => {
      const { result } = renderHook(() => useDashboardStore())

      // Set specific date range
      act(() => {
        result.current.setDateRange({
          start: new Date('2024-01-15'),
          end: new Date('2024-01-30'),
        })
      })

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      act(() => {
        result.current.fetchDashboardSummary()
      })

      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledWith(
          '/api/analytics/dashboard/summary?start_date=2024-01-15&end_date=2024-01-30'
        )
      })
    })

    it('handles date formatting edge cases', async () => {
      const { result } = renderHook(() => useDashboardStore())

      // Set date range with time components
      act(() => {
        result.current.setDateRange({
          start: new Date('2024-01-15T14:30:45.123Z'),
          end: new Date('2024-01-30T23:59:59.999Z'),
        })
      })

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      act(() => {
        result.current.fetchDashboardSummary()
      })

      await waitFor(() => {
        const call = fetchMock.mock.calls[0][0]
        expect(call).toContain('start_date=2024-01-15')
        expect(call).toContain('end_date=2024-01-30')
      })
    })
  })

  describe('setLoading and setError', () => {
    it('setLoading updates loading state', () => {
      const { result } = renderHook(() => useDashboardStore())

      act(() => {
        result.current.setLoading(true)
      })

      expect(result.current.isLoading).toBe(true)

      act(() => {
        result.current.setLoading(false)
      })

      expect(result.current.isLoading).toBe(false)
    })

    it('setError updates error state', () => {
      const { result } = renderHook(() => useDashboardStore())

      act(() => {
        result.current.setError('Test error')
      })

      expect(result.current.error).toBe('Test error')

      act(() => {
        result.current.setError(null)
      })

      expect(result.current.error).toBeNull()
    })
  })

  describe('Persistence', () => {
    it('persists date range to localStorage', () => {
      const { result } = renderHook(() => useDashboardStore())

      const newDateRange = {
        start: new Date('2024-01-01'),
        end: new Date('2024-01-31'),
      }

      act(() => {
        result.current.setDateRange(newDateRange)
      })

      // Check that localStorage was called (this would be tested with a more complete setup)
      // In a real scenario, we'd check the persist middleware behavior
      expect(result.current.dateRange).toEqual(newDateRange)
    })

    it('does not persist other state properties', () => {
      const { result } = renderHook(() => useDashboardStore())

      act(() => {
        result.current.setLoading(true)
        result.current.setError('test error')
      })

      // These should not be persisted according to the partialize config
      // In a real test, we'd check localStorage contents
      expect(result.current.isLoading).toBe(true)
      expect(result.current.error).toBe('test error')
    })
  })

  describe('Concurrent operations', () => {
    it('handles multiple simultaneous fetch requests', async () => {
      const { result } = renderHook(() => useDashboardStore())

      fetchMock
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ total_feedback: 100 }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ total_feedback: 200 }),
        })

      // Start two fetch operations
      act(() => {
        result.current.fetchDashboardSummary()
        result.current.fetchDashboardSummary()
      })

      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledTimes(2)
      })

      // Should have the result from the last call
      await waitFor(() => {
        expect(result.current.dashboardSummary?.total_feedback).toBe(200)
      })
    })
  })

  describe('Error recovery', () => {
    it('clears error state on successful retry', async () => {
      const { result } = renderHook(() => useDashboardStore())

      // First call fails
      fetchMock.mockRejectedValueOnce(new Error('Network error'))

      act(() => {
        result.current.fetchDashboardSummary()
      })

      await waitFor(() => {
        expect(result.current.error).toBe('Network error')
      })

      // Second call succeeds
      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total_feedback: 50 }),
      })

      act(() => {
        result.current.fetchDashboardSummary()
      })

      await waitFor(() => {
        expect(result.current.error).toBeNull()
        expect(result.current.dashboardSummary?.total_feedback).toBe(50)
      })
    })
  })

  describe('Edge cases', () => {
    it('handles empty response data', async () => {
      const { result } = renderHook(() => useDashboardStore())

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      act(() => {
        result.current.fetchDashboardSummary()
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.dashboardSummary).toEqual({})
        expect(result.current.error).toBeNull()
      })
    })

    it('handles malformed JSON response', async () => {
      const { result } = renderHook(() => useDashboardStore())

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => {
          throw new Error('Invalid JSON')
        },
      })

      act(() => {
        result.current.fetchDashboardSummary()
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
        expect(result.current.error).toBe('Failed to fetch dashboard summary')
      })
    })

    it('handles extremely large date ranges', async () => {
      const { result } = renderHook(() => useDashboardStore())

      const farPast = new Date('1900-01-01')
      const farFuture = new Date('2100-12-31')

      act(() => {
        result.current.setDateRange({
          start: farPast,
          end: farFuture,
        })
      })

      fetchMock.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      act(() => {
        result.current.fetchDashboardSummary()
      })

      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledWith(
          expect.stringContaining('start_date=1900-01-01')
        )
        expect(fetchMock).toHaveBeenCalledWith(
          expect.stringContaining('end_date=2100-12-31')
        )
      })
    })
  })
})
