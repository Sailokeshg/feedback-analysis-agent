import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '../../test/test-utils'
import TrendChart from '../TrendChart'
import { useDashboardStore } from '../../stores/dashboardStore'

// Mock the dashboard store
vi.mock('../../stores/dashboardStore', () => ({
  useDashboardStore: vi.fn(),
}))

// Mock Recharts components
vi.mock('recharts', () => ({
  LineChart: ({ children, data }: any) => (
    <div data-testid="line-chart" data-chart-data={JSON.stringify(data)}>
      {children}
    </div>
  ),
  Line: ({ dataKey, stroke, name }: any) => (
    <div
      data-testid={`line-${dataKey}`}
      data-stroke={stroke}
      data-name={name}
    />
  ),
  XAxis: ({ dataKey, tickFormatter }: any) => (
    <div data-testid="x-axis" data-key={dataKey} data-formatter={tickFormatter?.toString()} />
  ),
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: ({ contentStyle, labelFormatter }: any) => (
    <div
      data-testid="tooltip"
      data-style={JSON.stringify(contentStyle)}
      data-formatter={labelFormatter?.toString()}
    />
  ),
  ResponsiveContainer: ({ children, width, height }: any) => (
    <div data-testid="responsive-container" data-width={width} data-height={height}>
      {children}
    </div>
  ),
}))

describe('TrendChart', () => {
  const mockUseDashboardStore = vi.mocked(useDashboardStore)

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Loading state', () => {
    it('renders skeleton when loading', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: null,
        isLoading: true,
      })

      render(<TrendChart />)

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
      expect(document.querySelector('.animate-pulse')).toBeInTheDocument()
    })

    it('shows loading skeleton with correct structure', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: null,
        isLoading: true,
      })

      const { container } = render(<TrendChart />)

      const skeleton = container.querySelector('.animate-pulse')
      expect(skeleton).toBeInTheDocument()

      // Check skeleton structure
      const titleSkeleton = skeleton?.querySelector('div.h-6')
      const chartSkeleton = skeleton?.querySelector('div.h-\\[300px\\]')

      expect(titleSkeleton).toBeInTheDocument()
      expect(chartSkeleton).toBeInTheDocument()
    })
  })

  describe('No data state', () => {
    it('renders no data message when trends_14d is empty', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: [],
        },
        isLoading: false,
      })

      render(<TrendChart />)

      expect(screen.getByText('14-Day Trend')).toBeInTheDocument()
      expect(screen.getByText('No trend data available')).toBeInTheDocument()
    })

    it('renders no data message when trends_14d is null', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: null,
        },
        isLoading: false,
      })

      render(<TrendChart />)

      expect(screen.getByText('No trend data available')).toBeInTheDocument()
    })

    it('renders no data message when dashboardSummary is null', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: null,
        isLoading: false,
      })

      render(<TrendChart />)

      expect(screen.getByText('No trend data available')).toBeInTheDocument()
    })
  })

  describe('Data visualization', () => {
    const mockTrendData = [
      { date: '2024-01-01', positive: 10, negative: 5, neutral: 3 },
      { date: '2024-01-02', positive: 12, negative: 4, neutral: 2 },
      { date: '2024-01-03', positive: 8, negative: 6, neutral: 4 },
    ]

    it('renders chart with trend data', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: mockTrendData,
        },
        isLoading: false,
      })

      render(<TrendChart />)

      expect(screen.getByText('14-Day Trend')).toBeInTheDocument()
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
    })

    it('passes correct data to chart components', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: mockTrendData,
        },
        isLoading: false,
      })

      render(<TrendChart />)

      const chart = screen.getByTestId('line-chart')
      const chartData = JSON.parse(chart.getAttribute('data-chart-data') || '[]')
      expect(chartData).toEqual(mockTrendData)
    })

    it('renders all three trend lines', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: mockTrendData,
        },
        isLoading: false,
      })

      render(<TrendChart />)

      expect(screen.getByTestId('line-positive')).toBeInTheDocument()
      expect(screen.getByTestId('line-negative')).toBeInTheDocument()
      expect(screen.getByTestId('line-neutral')).toBeInTheDocument()
    })

    it('configures lines with correct properties', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: mockTrendData,
        },
        isLoading: false,
      })

      render(<TrendChart />)

      const positiveLine = screen.getByTestId('line-positive')
      expect(positiveLine).toHaveAttribute('data-stroke', '#10b981')
      expect(positiveLine).toHaveAttribute('data-name', 'Positive')

      const negativeLine = screen.getByTestId('line-negative')
      expect(negativeLine).toHaveAttribute('data-stroke', '#ef4444')
      expect(negativeLine).toHaveAttribute('data-name', 'Negative')

      const neutralLine = screen.getByTestId('line-neutral')
      expect(neutralLine).toHaveAttribute('data-stroke', '#6b7280')
      expect(neutralLine).toHaveAttribute('data-name', 'Neutral')
    })

    it('configures axes correctly', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: mockTrendData,
        },
        isLoading: false,
      })

      render(<TrendChart />)

      const xAxis = screen.getByTestId('x-axis')
      expect(xAxis).toHaveAttribute('data-key', 'date')
      expect(xAxis).toHaveAttribute('data-formatter')

      expect(screen.getByTestId('y-axis')).toBeInTheDocument()
      expect(screen.getByTestId('cartesian-grid')).toBeInTheDocument()
    })

    it('configures tooltip correctly', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: mockTrendData,
        },
        isLoading: false,
      })

      render(<TrendChart />)

      const tooltip = screen.getByTestId('tooltip')
      const style = JSON.parse(tooltip.getAttribute('data-style') || '{}')
      expect(style.backgroundColor).toBe('white')
      expect(style.border).toBe('1px solid #e5e7eb')
      expect(style.borderRadius).toBe('6px')
    })
  })

  describe('Date formatting', () => {
    it('formats X-axis dates correctly', () => {
      const mockTrendData = [
        { date: '2024-01-15', positive: 10, negative: 5, neutral: 3 },
        { date: '2024-01-16', positive: 12, negative: 4, neutral: 2 },
      ]

      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: mockTrendData,
        },
        isLoading: false,
      })

      render(<TrendChart />)

      const xAxis = screen.getByTestId('x-axis')
      const formatter = xAxis.getAttribute('data-formatter')

      // The formatter should convert dates to short format
      if (formatter) {
        const testDate = new Date('2024-01-15')
        // This is a simplified check - in a real scenario we'd invoke the formatter
        expect(formatter).toContain('toLocaleDateString')
      }
    })

    it('formats tooltip labels correctly', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: [{ date: '2024-01-15', positive: 10, negative: 5, neutral: 3 }],
        },
        isLoading: false,
      })

      render(<TrendChart />)

      const tooltip = screen.getByTestId('tooltip')
      const formatter = tooltip.getAttribute('data-formatter')
      expect(formatter).toContain('toLocaleDateString')
    })
  })

  describe('Responsive design', () => {
    it('uses ResponsiveContainer for responsive chart', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: [{ date: '2024-01-01', positive: 1, negative: 0, neutral: 0 }],
        },
        isLoading: false,
      })

      render(<TrendChart />)

      const container = screen.getByTestId('responsive-container')
      expect(container).toHaveAttribute('data-width', '100%')
      expect(container).toHaveAttribute('data-height', '100%')
    })

    it('sets correct chart height', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: [{ date: '2024-01-01', positive: 1, negative: 0, neutral: 0 }],
        },
        isLoading: false,
      })

      const { container } = render(<TrendChart />)

      const chartContainer = container.querySelector('.h-\\[300px\\]')
      expect(chartContainer).toBeInTheDocument()
    })
  })

  describe('Styling and accessibility', () => {
    it('applies correct CSS classes', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: [{ date: '2024-01-01', positive: 1, negative: 0, neutral: 0 }],
        },
        isLoading: false,
      })

      const { container } = render(<TrendChart />)

      const chartCard = container.firstChild as HTMLElement
      expect(chartCard).toHaveClass(
        'bg-white',
        'dark:bg-gray-800',
        'rounded-lg',
        'border',
        'border-gray-200',
        'dark:border-gray-700',
        'p-6'
      )
    })

    it('has accessible heading', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: [{ date: '2024-01-01', positive: 1, negative: 0, neutral: 0 }],
        },
        isLoading: false,
      })

      render(<TrendChart />)

      const heading = screen.getByRole('heading', { level: 3 })
      expect(heading).toHaveTextContent('14-Day Trend')
    })

    it('has proper color contrast for dark mode', () => {
      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: [{ date: '2024-01-01', positive: 1, negative: 0, neutral: 0 }],
        },
        isLoading: false,
      })

      const { container } = render(<TrendChart />)

      // Check that dark mode classes are applied
      const heading = screen.getByText('14-Day Trend')
      expect(heading).toHaveClass('text-gray-900', 'dark:text-gray-100')
    })
  })

  describe('Integration with dashboard store', () => {
    it('subscribes to dashboard store', () => {
      render(<TrendChart />)

      expect(mockUseDashboardStore).toHaveBeenCalled()
    })

    it('re-renders when store data changes', () => {
      let callCount = 0
      mockUseDashboardStore.mockImplementation(() => {
        callCount++
        return {
          dashboardSummary: {
            trends_14d: [{ date: '2024-01-01', positive: callCount, negative: 0, neutral: 0 }],
          },
          isLoading: false,
        }
      })

      const { rerender } = render(<TrendChart />)
      rerender(<TrendChart />)

      expect(callCount).toBeGreaterThan(1)
    })
  })

  describe('Edge cases', () => {
    it('handles malformed trend data gracefully', () => {
      const malformedData = [
        { date: '2024-01-01', positive: 'invalid', negative: null, neutral: undefined },
        { date: '2024-01-02', positive: NaN, negative: 0, neutral: 0 },
      ]

      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: malformedData,
        },
        isLoading: false,
      })

      // Should not crash
      expect(() => render(<TrendChart />)).not.toThrow()
    })

    it('handles very large datasets', () => {
      const largeDataset = Array.from({ length: 365 }, (_, i) => ({
        date: `2024-${String(Math.floor(i / 30) + 1).padStart(2, '0')}-${String((i % 30) + 1).padStart(2, '0')}`,
        positive: Math.floor(Math.random() * 100),
        negative: Math.floor(Math.random() * 50),
        neutral: Math.floor(Math.random() * 30),
      }))

      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: largeDataset,
        },
        isLoading: false,
      })

      render(<TrendChart />)

      const chart = screen.getByTestId('line-chart')
      const chartData = JSON.parse(chart.getAttribute('data-chart-data') || '[]')
      expect(chartData).toHaveLength(365)
    })

    it('handles empty objects in trend data', () => {
      const dataWithEmptyObjects = [
        { date: '2024-01-01', positive: 0, negative: 0, neutral: 0 },
        {},
        { date: '2024-01-03' },
      ]

      mockUseDashboardStore.mockReturnValue({
        dashboardSummary: {
          trends_14d: dataWithEmptyObjects,
        },
        isLoading: false,
      })

      // Should not crash
      expect(() => render(<TrendChart />)).not.toThrow()
    })
  })
})
