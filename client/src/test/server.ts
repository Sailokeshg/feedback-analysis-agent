import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { createMockFeedback, createMockTopic, createMockAnalyticsData, sampleFeedbackList, sampleTopicsData } from './test-utils'

// Mock API handlers
export const handlers = [
  // Feedback endpoints
  http.get('/api/feedback', ({ request }) => {
    const url = new URL(request.url)
    const page = url.searchParams.get('page') || '1'
    const pageSize = url.searchParams.get('page_size') || '10'
    const source = req.url.searchParams.get('source')
    const startDate = req.url.searchParams.get('start_date')
    const endDate = req.url.searchParams.get('end_date')

    let filteredFeedback = [...sampleFeedbackList]

    // Apply filters
    if (source) {
      filteredFeedback = filteredFeedback.filter(f => f.source === source)
    }

    if (startDate || endDate) {
      filteredFeedback = filteredFeedback.filter(f => {
        const feedbackDate = new Date(f.created_at)
        const start = startDate ? new Date(startDate) : new Date('2020-01-01')
        const end = endDate ? new Date(endDate) : new Date('2030-01-01')
        return feedbackDate >= start && feedbackDate <= end
      })
    }

    const startIndex = (parseInt(page) - 1) * parseInt(pageSize)
    const endIndex = startIndex + parseInt(pageSize)
    const paginatedFeedback = filteredFeedback.slice(startIndex, endIndex)

    return res(
      ctx.json({
        items: paginatedFeedback,
        total: filteredFeedback.length,
        page: parseInt(page),
        page_size: parseInt(pageSize),
        has_next: endIndex < filteredFeedback.length,
      })
    )
  }),

  rest.get('/api/feedback/:id', (req, res, ctx) => {
    const { id } = req.params
    const feedback = sampleFeedbackList.find(f => f.id === id)

    if (!feedback) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Feedback not found' })
      )
    }

    return res(ctx.json(feedback))
  }),

  rest.post('/api/feedback', (req, res, ctx) => {
    const body = req.body as any

    if (!body.text || !body.source) {
      return res(
        ctx.status(422),
        ctx.json({
          detail: [
            {
              loc: ['body', 'text'],
              msg: 'Field required',
              type: 'value_error.missing'
            }
          ]
        })
      )
    }

    const newFeedback = createMockFeedback({
      id: `new-feedback-${Date.now()}`,
      ...body,
    })

    return res(ctx.status(201), ctx.json(newFeedback))
  }),

  // Topics endpoints
  rest.get('/api/topics', (req, res, ctx) => {
    return res(ctx.json(sampleTopicsData))
  }),

  rest.get('/api/topics/:id', (req, res, ctx) => {
    const { id } = req.params
    const topic = sampleTopicsData.find(t => t.id === parseInt(id))

    if (!topic) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Topic not found' })
      )
    }

    return res(ctx.json(topic))
  }),

  rest.post('/api/topics', (req, res, ctx) => {
    const body = req.body as any

    if (!body.label || !body.keywords) {
      return res(
        ctx.status(422),
        ctx.json({
          detail: 'Missing required fields: label and keywords'
        })
      )
    }

    const newTopic = createMockTopic({
      id: sampleTopicsData.length + 1,
      ...body,
    })

    return res(ctx.status(201), ctx.json(newTopic))
  }),

  rest.put('/api/topics/:id', (req, res, ctx) => {
    const { id } = req.params
    const body = req.body as any
    const topicIndex = sampleTopicsData.findIndex(t => t.id === parseInt(id))

    if (topicIndex === -1) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Topic not found' })
      )
    }

    const updatedTopic = {
      ...sampleTopicsData[topicIndex],
      ...body,
    }

    return res(ctx.json(updatedTopic))
  }),

  rest.delete('/api/topics/:id', (req, res, ctx) => {
    const { id } = req.params
    const topicExists = sampleTopicsData.some(t => t.id === parseInt(id))

    if (!topicExists) {
      return res(
        ctx.status(404),
        ctx.json({ detail: 'Topic not found' })
      )
    }

    return res(ctx.status(204))
  }),

  // Trends endpoints
  rest.get('/api/trends/sentiment', (req, res, ctx) => {
    const groupBy = req.url.searchParams.get('group_by') || 'day'

    if (!['day', 'week', 'month'].includes(groupBy)) {
      return res(
        ctx.status(400),
        ctx.json({ detail: 'Invalid group_by parameter. Must be day, week, or month.' })
      )
    }

    const mockTrends = [
      { period: '2024-01-01', positive_count: 10, negative_count: 5, neutral_count: 3 },
      { period: '2024-01-02', positive_count: 12, negative_count: 4, neutral_count: 2 },
      { period: '2024-01-03', positive_count: 8, negative_count: 6, neutral_count: 4 },
    ]

    return res(ctx.json(mockTrends))
  }),

  rest.get('/api/trends/topics', (req, res, ctx) => {
    const mockTopicDistribution = [
      { id: 1, label: 'Quality', feedback_count: 40, percentage: 26.7 },
      { id: 2, label: 'Support', feedback_count: 35, percentage: 23.3 },
      { id: 3, label: 'Pricing', feedback_count: 30, percentage: 20.0 },
      { id: 4, label: 'Features', feedback_count: 25, percentage: 16.7 },
      { id: 5, label: 'Usability', feedback_count: 20, percentage: 13.3 },
    ]

    return res(ctx.json(mockTopicDistribution))
  }),

  rest.get('/api/trends/customers', (req, res, ctx) => {
    const mockCustomerStats = [
      { customer_id: 'CUST_001', feedback_count: 5, avg_sentiment: 0.7 },
      { customer_id: 'CUST_002', feedback_count: 3, avg_sentiment: 0.4 },
      { customer_id: 'CUST_003', feedback_count: 8, avg_sentiment: 0.8 },
    ]

    return res(ctx.json(mockCustomerStats))
  }),

  // Query/Chat endpoints
  rest.post('/api/query/chat', async (req, res, ctx) => {
    const body = await req.json()

    if (!body.query || body.query.trim() === '') {
      return res(
        ctx.status(400),
        ctx.json({ detail: 'Query cannot be empty' })
      )
    }

    if (body.query.length > 1000) {
      return res(
        ctx.status(400),
        ctx.json({ detail: 'Query too long. Maximum 1000 characters.' })
      )
    }

    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 100))

    return res(ctx.json({
      response: `Based on the feedback analysis, here's what I found regarding "${body.query}"...`,
      sources: ['feedback_1', 'feedback_2', 'feedback_3'],
      confidence: 0.85,
      timestamp: new Date().toISOString(),
    }))
  }),

  // Upload endpoints
  rest.post('/api/upload/csv', (req, res, ctx) => {
    // Simulate file processing
    return res(ctx.json({
      processed_count: 150,
      errors: [],
      status: 'completed'
    }))
  }),

  rest.post('/api/upload/jsonl', (req, res, ctx) => {
    // Simulate file processing
    return res(ctx.json({
      processed_count: 200,
      errors: [],
      status: 'completed'
    }))
  }),

  // Health check
  rest.get('/health', (req, res, ctx) => {
    return res(ctx.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '1.0.0'
    }))
  }),
]

// Setup server
export const server = setupServer(...handlers)

// Test utilities for MSW
export const setupMSW = () => {
  beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
  afterEach(() => server.resetHandlers())
  afterAll(() => server.close())
}
