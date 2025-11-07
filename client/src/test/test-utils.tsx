import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Custom render function that includes common providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }

// Custom matchers for common assertions
export const matchers = {
  toBeVisible: (element: HTMLElement) => {
    const isVisible = element.offsetWidth > 0 && element.offsetHeight > 0
    return {
      pass: isVisible,
      message: () => `Expected element to be visible, but it is not`,
    }
  },

  toHaveTextContent: (element: HTMLElement, expectedText: string | RegExp) => {
    const textContent = element.textContent || ''
    const pass = typeof expectedText === 'string'
      ? textContent.includes(expectedText)
      : expectedText.test(textContent)

    return {
      pass,
      message: () => `Expected element to contain text "${expectedText}", but it contains "${textContent}"`,
    }
  },

  toHaveClass: (element: HTMLElement, className: string) => {
    const hasClass = element.classList.contains(className)
    return {
      pass: hasClass,
      message: () => `Expected element to have class "${className}", but it does not`,
    }
  },

  toHaveAttribute: (element: HTMLElement, attribute: string, value?: string) => {
    const hasAttribute = element.hasAttribute(attribute)
    const attributeValue = element.getAttribute(attribute)

    if (value === undefined) {
      return {
        pass: hasAttribute,
        message: () => `Expected element to have attribute "${attribute}"`,
      }
    }

    const pass = hasAttribute && attributeValue === value
    return {
      pass,
      message: () => `Expected element to have attribute "${attribute}" with value "${value}", but got "${attributeValue}"`,
    }
  },
}

// Mock data factories for testing
export const createMockFeedback = (overrides = {}) => ({
  id: 'test-feedback-id',
  source: 'website',
  text: 'This is a test feedback message',
  customer_id: 'customer_123',
  created_at: '2024-01-15T10:30:00Z',
  sentiment: 1,
  sentiment_score: 0.85,
  topic_cluster: 'product_quality',
  ...overrides,
})

export const createMockTopic = (overrides = {}) => ({
  id: 1,
  label: 'Product Quality',
  keywords: ['quality', 'product', 'excellent'],
  feedback_count: 25,
  ...overrides,
})

export const createMockAnalyticsData = (overrides = {}) => ({
  total_feedback: 150,
  sentiment_distribution: {
    positive: 45,
    negative: 30,
    neutral: 25,
  },
  top_topics: [
    { label: 'Quality', count: 40, percentage: 26.7 },
    { label: 'Pricing', count: 35, percentage: 23.3 },
    { label: 'Support', count: 25, percentage: 16.7 },
  ],
  trends: [
    { period: '2024-01-01', positive: 10, negative: 5, neutral: 3 },
    { period: '2024-01-02', positive: 12, negative: 4, neutral: 2 },
  ],
  ...overrides,
})

export const createMockKPIData = (overrides = {}) => ({
  totalFeedback: 150,
  positiveSentiment: 45,
  negativeSentiment: 30,
  neutralSentiment: 25,
  avgSentimentScore: 0.65,
  topTopic: 'Quality',
  feedbackGrowth: 12.5,
  ...overrides,
})

// Mock API response helpers
export const mockApiResponse = (data: any, status = 200) => ({
  data,
  status,
  statusText: status === 200 ? 'OK' : 'Error',
})

export const mockApiError = (message: string, status = 500) => ({
  response: {
    data: { detail: message },
    status,
  },
})

// Test data sets
export const sampleFeedbackList = [
  createMockFeedback({
    id: 'fb-1',
    text: 'Amazing product! Highly recommend.',
    sentiment: 1,
    sentiment_score: 0.92,
  }),
  createMockFeedback({
    id: 'fb-2',
    text: 'Poor quality, disappointed with purchase.',
    sentiment: -1,
    sentiment_score: 0.78,
  }),
  createMockFeedback({
    id: 'fb-3',
    text: 'It works as expected.',
    sentiment: 0,
    sentiment_score: 0.45,
  }),
]

export const sampleTopicsData = [
  createMockTopic({
    id: 1,
    label: 'Product Quality',
    feedback_count: 45,
  }),
  createMockTopic({
    id: 2,
    label: 'Customer Support',
    feedback_count: 32,
  }),
  createMockTopic({
    id: 3,
    label: 'Pricing',
    feedback_count: 28,
  }),
]

// Utility functions for common test operations
export const waitForLoadingToFinish = async () => {
  // Wait for any loading states to finish
  await new Promise(resolve => setTimeout(resolve, 0))
}

export const createMockIntersectionObserver = () => {
  const mockIntersectionObserver = jest.fn()
  mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  })
  window.IntersectionObserver = mockIntersectionObserver
  return mockIntersectionObserver
}

export const createMockResizeObserver = () => {
  const mockResizeObserver = jest.fn()
  mockResizeObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  })
  window.ResizeObserver = mockResizeObserver
  return mockResizeObserver
}

// Setup function for common mocks
export const setupTestEnvironment = () => {
  createMockIntersectionObserver()
  createMockResizeObserver()

  // Mock console methods to reduce noise in tests
  const originalConsoleError = console.error
  const originalConsoleWarn = console.warn

  beforeAll(() => {
    console.error = jest.fn()
    console.warn = jest.fn()
  })

  afterAll(() => {
    console.error = originalConsoleError
    console.warn = originalConsoleWarn
  })
}
