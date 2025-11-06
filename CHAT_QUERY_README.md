# Chat Query Endpoint Implementation

A high-performance, concurrent-safe API endpoint for querying customer feedback using LangChain agents with advanced filtering, token limits, and timeout controls.

## Overview

The `/chat/query` endpoint provides natural language querying of customer feedback data with:

- **Structured Filtering**: Apply date ranges, sentiment, topics, sources, customers, and languages
- **Citation Tracking**: Automatically extract and validate feedback_id citations
- **Token Limits**: Prevent abuse with configurable token and length limits
- **Timeout Controls**: Prevent runaway requests with configurable timeouts
- **Concurrent Safety**: Optimized for multiple simultaneous requests

## API Specification

### Endpoint

```
POST /api/v1/chat/query
```

### Request Format

```json
{
  "question": "What are the main topics in customer feedback?",
  "filters": {
    "date_range": {
      "start_date": "2024-01-01",
      "end_date": "2024-12-31"
    },
    "sentiment": -1,
    "topic_ids": [1, 2, 3],
    "source": "web",
    "customer_id": "12345",
    "language": "en"
  }
}
```

### Response Format

```json
{
  "answer": "Based on the feedback data, the main topics are product quality and customer service. As one customer stated (feedback_id: 123e4567-e89b-12d3-a456-426614174000): 'The product quality is excellent but service could be better.'",
  "citations": [
    {
      "feedback_id": "123e4567-e89b-12d3-a456-426614174000",
      "topic_id": 1
    },
    {
      "feedback_id": "987fcdeb-51a2-43d0-8f12-345678901234",
      "topic_id": 2
    }
  ]
}
```

## Request/Response Models

### ChatQueryRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | Yes | The natural language question to ask |
| `filters` | QueryFilters | No | Optional filters to apply |

### QueryFilters

| Field | Type | Description |
|-------|------|-------------|
| `date_range` | DateRangeFilter | Date range filter |
| `sentiment` | integer | Sentiment filter (-1, 0, 1) |
| `topic_ids` | array | List of topic IDs |
| `source` | string | Feedback source filter |
| `customer_id` | string | Customer ID filter |
| `language` | string | Language filter |

### DateRangeFilter

| Field | Type | Description |
|-------|------|-------------|
| `start_date` | string | Start date (YYYY-MM-DD) |
| `end_date` | string | End date (YYYY-MM-DD) |

### ChatQueryResponse

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Agent's response with citations |
| `citations` | array | List of extracted citations |

### Citation

| Field | Type | Description |
|-------|------|-------------|
| `feedback_id` | string | UUID of cited feedback |
| `topic_id` | integer | Associated topic ID (null if none) |

## Configuration & Limits

### Token Limits

```python
MAX_TOKENS = 4000          # Total tokens per request
MAX_QUESTION_LENGTH = 1000  # Max question characters
REQUEST_TIMEOUT = 30        # Max processing time in seconds
```

### Rate Limiting

The endpoint inherits rate limiting from the global middleware:

```python
RATE_LIMIT_REQUESTS_PER_MINUTE = 60
RATE_LIMIT_BURST = 10
```

## Implementation Details

### Filter Processing

Filters are applied by modifying the query prompt sent to the LangChain agent:

```python
def apply_filters_to_query(query: str, filters: Optional[QueryFilters]) -> str:
    # Converts filters to descriptive text
    # Example: "What are topics? (filtered to show only feedback from 2024-01-01 until 2024-12-31 and with negative sentiment)"
```

### Citation Extraction

Citations are automatically extracted from agent responses using regex:

```python
feedback_id_pattern = r'feedback_id[:\s]+([a-f0-9\-]{36})'
```

Each citation is validated against the database to retrieve the associated `topic_id`.

### Concurrent Optimization

- **Async Agent Initialization**: Thread-safe singleton pattern prevents blocking
- **Thread Pool Execution**: Agent processing runs in thread pool to not block event loop
- **Timeout Controls**: Configurable timeouts prevent resource exhaustion
- **Connection Pooling**: Database connections are properly pooled

### Error Handling

- **Token Limit Exceeded**: HTTP 413 with descriptive message
- **Timeout**: HTTP 408 with timeout duration
- **Rate Limited**: HTTP 429 with retry-after header
- **Invalid Input**: HTTP 422 with validation details
- **Server Error**: HTTP 500 with error details

## Usage Examples

### Basic Query

```bash
curl -X POST "http://localhost:8000/api/v1/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main customer complaints?"
  }'
```

### Filtered Query

```bash
curl -X POST "http://localhost:8000/api/v1/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Show me recent negative feedback",
    "filters": {
      "date_range": {"start_date": "2024-01-01"},
      "sentiment": -1
    }
  }'
```

### Complex Filtering

```bash
curl -X POST "http://localhost:8000/api/v1/chat/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What do customers say about our mobile app?",
    "filters": {
      "topic_ids": [5, 12],
      "source": "mobile",
      "language": "en"
    }
  }'
```

## Load Testing

### Test Script

The included `load_test_chat.py` script tests concurrent performance:

```bash
python3 load_test_chat.py
```

### Performance Targets

- **Concurrent Requests**: 5 simultaneous requests on dev machine
- **Success Rate**: >80% for valid requests
- **Response Time**: <30 seconds average
- **Throughput**: Multiple requests/second

### Test Results Example

```
LOAD TEST RESULTS
==================================================
Total Requests: 5
Successful: 5
Success Rate: 100.0%
Total Test Time: 12.34s
Batch Time: 8.92s
Requests/Second: 0.56

Response Times:
  Average: 15.67s
  Min: 12.34s
  Max: 18.90s
  Median: 15.23s

PERFORMANCE ASSESSMENT:
  ✅ EXCELLENT: High success rate and acceptable response times
```

## Security & Validation

### Input Validation

- **Question Length**: Maximum 1000 characters
- **Token Estimation**: Rough token counting prevents abuse
- **Filter Validation**: Type checking and range validation
- **SQL Injection Prevention**: Parameterized queries throughout

### Output Validation

- **Citation Verification**: All cited feedback_ids validated against database
- **Grounding Checks**: Agent responses validated for proper data grounding
- **Content Filtering**: Sensitive information redaction

## Monitoring & Observability

### Performance Headers

```http
X-Process-Time: 2.34
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640995200
```

### Logging

- **Request Logging**: Question, filters, and processing time
- **Error Logging**: Detailed error information with context
- **Performance Logging**: Response times and citation counts

## Future Enhancements

- **Streaming Responses**: Server-sent events for real-time answers
- **Query Caching**: Intelligent caching of similar queries
- **Advanced Filtering**: Geographic, demographic, and behavioral filters
- **Analytics Integration**: Query pattern analysis and suggestions
- **Multi-modal Queries**: Support for image and document queries

## Testing

### Unit Tests

```bash
python3 test_chat_endpoint.py
```

Tests cover:
- ✅ Model definitions and validation
- ✅ Filter application logic
- ✅ Citation extraction
- ✅ Token limit enforcement
- ✅ Error handling

### Load Tests

```bash
python3 load_test_chat.py
```

Validates concurrent request handling and performance characteristics.

---

**Note**: This implementation ensures reliable, performant querying of feedback data with proper citation tracking and abuse prevention measures.
