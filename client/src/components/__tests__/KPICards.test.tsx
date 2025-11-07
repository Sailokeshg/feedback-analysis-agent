import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '../../test/test-utils'
import KPICards from '../KPICards'
import { useDashboardStore } from '../../stores/dashboardStore'

// Mock the dashboard store
vi.mock('../../stores/dashboardStore', () => ({
  useDashboardStore: vi.fn(),
}))

describe('KPICards', () => {
  const mockUseDashboardStore = vi.mocked(useDashboardStore)

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('KPICard component', () => {
    it('renders loading state correctly', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: null,
        isLoading: true,
      })

      render(<KPICards />)

      // Should show loading skeletons
      const loadingElements = document.querySelectorAll('.animate-pulse')
      expect(loadingElements.length).toBe(3) // One for each KPI card

      // Should not show actual content
      expect(screen.queryByText('Total Feedback')).not.toBeInTheDocument()
      expect(screen.queryByText('Negative Feedback')).not.toBeInTheDocument()
      expect(screen.queryByText('Topics Identified')).not.toBeInTheDocument()
    })

    it('renders KPI data correctly when loaded', () => {
      const mockSummary = {
        total_feedback: 150,
        negative_percentage: 23.5,
        topics_count: 12,
      }

      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: mockSummary,
        isLoading: false,
      })

      render(<KPICards />)

      // Check Total Feedback card
      expect(screen.getByText('Total Feedback')).toBeInTheDocument()
      expect(screen.getByText('150')).toBeInTheDocument()
      expect(screen.getByText('All time')).toBeInTheDocument()

      // Check Negative Feedback card
      expect(screen.getByText('Negative Feedback')).toBeInTheDocument()
      expect(screen.getByText('23.5%')).toBeInTheDocument()
      expect(screen.getByText('Of total feedback')).toBeInTheDocument()

      // Check Topics Identified card
      expect(screen.getByText('Topics Identified')).toBeInTheDocument()
      expect(screen.getByText('12')).toBeInTheDocument()
      expect(screen.getByText('Unique topics')).toBeInTheDocument()
    })

    it('handles zero values correctly', () => {
      const mockSummary = {
        total_feedback: 0,
        negative_percentage: 0,
        topics_count: 0,
      }

      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: mockSummary,
        isLoading: false,
      })

      render(<KPICards />)

      expect(screen.getByText('0')).toBeInTheDocument()
      expect(screen.getByText('0%')).toBeInTheDocument()
    })

    it('handles null/undefined dashboard summary gracefully', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: null,
        isLoading: false,
      })

      render(<KPICards />)

      // Should show zeros when data is null
      expect(screen.getAllByText('0')).toHaveLength(2) // Total feedback and topics
      expect(screen.getByText('0%')).toBeInTheDocument()
    })

    it('handles partial dashboard summary data', () => {
      const mockSummary = {
        total_feedback: 100,
        // negative_percentage and topics_count are undefined
      }

      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: mockSummary,
        isLoading: false,
      })

      render(<KPICards />)

      expect(screen.getByText('100')).toBeInTheDocument()
      expect(screen.getByText('0%')).toBeInTheDocument()
      expect(screen.getAllByText('0')).toHaveLength(1) // Only topics should be 0
    })

    it('applies correct CSS classes', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          total_feedback: 50,
          negative_percentage: 10.0,
          topics_count: 5,
        },
        isLoading: false,
      })

      const { container } = render(<KPICards />)

      // Check grid layout
      const gridElement = container.firstChild
      expect(gridElement).toHaveClass('grid', 'grid-cols-1', 'md:grid-cols-3', 'gap-6', 'mb-6')

      // Check individual card styling
      const cards = container.querySelectorAll('.bg-white')
      expect(cards).toHaveLength(3)

      cards.forEach(card => {
        expect(card).toHaveClass(
          'bg-white',
          'dark:bg-gray-800',
          'rounded-lg',
          'border',
          'border-gray-200',
          'dark:border-gray-700',
          'p-6'
        )
      })
    })

    it('displays decimal precision correctly for percentages', () => {
      const mockSummary = {
        total_feedback: 200,
        negative_percentage: 15.789,
        topics_count: 8,
      }

      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: mockSummary,
        isLoading: false,
      })

      render(<KPICards />)

      expect(screen.getByText('15.8%')).toBeInTheDocument()
    })

    it('handles negative percentage values', () => {
      const mockSummary = {
        total_feedback: 100,
        negative_percentage: -5.2, // Shouldn't happen in real data, but test edge case
        topics_count: 3,
      }

      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: mockSummary,
        isLoading: false,
      })

      render(<KPICards />)

      expect(screen.getByText('-5.2%')).toBeInTheDocument()
    })

    it('handles very large numbers', () => {
      const mockSummary = {
        total_feedback: 1000000,
        negative_percentage: 99.99,
        topics_count: 500,
      }

      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: mockSummary,
        isLoading: false,
      })

      render(<KPICards />)

      expect(screen.getByText('1000000')).toBeInTheDocument()
      expect(screen.getByText('100.0%')).toBeInTheDocument()
      expect(screen.getByText('500')).toBeInTheDocument()
    })

    it('is accessible with proper headings and structure', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          total_feedback: 75,
          negative_percentage: 12.5,
          topics_count: 6,
        },
        isLoading: false,
      })

      render(<KPICards />)

      // Check that headings are present
      const headings = screen.getAllByRole('heading', { level: 3 })
      expect(headings).toHaveLength(3)
      expect(headings[0]).toHaveTextContent('Total Feedback')
      expect(headings[1]).toHaveTextContent('Negative Feedback')
      expect(headings[2]).toHaveTextContent('Topics Identified')
    })

    it('updates when store data changes', () => {
      const { rerender } = render(<KPICards />)

      // Initial render with loading
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: null,
        isLoading: true,
      })

      rerender(<KPICards />)

      expect(document.querySelectorAll('.animate-pulse')).toHaveLength(3)

      // Update with data
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          total_feedback: 42,
          negative_percentage: 8.3,
          topics_count: 4,
        },
        isLoading: false,
      })

      rerender(<KPICards />)

      expect(screen.getByText('42')).toBeInTheDocument()
      expect(screen.getByText('8.3%')).toBeInTheDocument()
      expect(screen.getByText('4')).toBeInTheDocument()
    })
  })

  describe('Integration with dashboard store', () => {
    it('subscribes to dashboard store changes', () => {
      render(<KPICards />)

      expect(mockUseDashboardStore).toHaveBeenCalledTimes(1)
    })

    it('re-renders when store state changes', () => {
      let renderCount = 0
      mockUseDashboardStore.mockImplementation(() => {
        renderCount++
        return {
          dashboardSummary: {
            total_feedback: renderCount,
            negative_percentage: 10.0,
            topics_count: 3,
          },
          isLoading: false,
        }
      })

      const { rerender } = render(<KPICards />)
      rerender(<KPICards />)

      expect(renderCount).toBeGreaterThan(1)
    })
  })

  describe('Responsive design', () => {
    it('uses correct grid classes for responsive layout', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          total_feedback: 100,
          negative_percentage: 20.0,
          topics_count: 8,
        },
        isLoading: false,
      })

      const { container } = render(<KPICards />)

      const gridContainer = container.firstChild
      expect(gridContainer).toHaveClass('grid-cols-1') // Mobile first
      expect(gridContainer).toHaveClass('md:grid-cols-3') // Desktop layout
    })
  })
})
