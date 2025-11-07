# API Reference

## Overview

The AI Customer Insights Agent provides a REST API for managing customer feedback, performing analytics, and interacting with the AI assistant. All endpoints return JSON responses and use standard HTTP status codes.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, no authentication is required. Authentication will be added in future versions.

## Content Types
- **Request**: `application/json`
- **Response**: `application/json`
- **File Upload**: `multipart/form-data`

---

## Feedback Endpoints

### Create Feedback
Create a new feedback item.

```http
POST /api/feedback
Content-Type: application/json

{
  "source": "website",
  "text": "Great product! Highly recommend.",
  "customer_id": "customer_123",
  "meta": {
    "rating": 5,
    "category": "product"
  }
}
```

**Response (201):**
```json
{
  "id": "fb_550e8400-e29b-41d4-a716-446655440000",
  "source": "website",
  "text": "Great product! Highly recommend.",
  "customer_id": "customer_123",
  "created_at": "2024-01-15T10:30:00.123456Z",
  "normalized_text": "great product highly recommend",
  "detected_language": "en",
  "meta": {
    "rating": 5,
    "category": "product"
  }
}
```

### Get Feedback List
Retrieve paginated feedback items with optional filtering.

```http
GET /api/feedback?page=1&page_size=50&source=website&start_date=2024-01-01&end_date=2024-12-31
```

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Items per page (default: 50, max: 1000)
- `source` (string, optional): Filter by source
- `customer_id` (string, optional): Filter by customer ID
- `start_date` (string, optional): Start date (YYYY-MM-DD)
- `end_date` (string, optional): End date (YYYY-MM-DD)

**Response (200):**
```json
{
  "items": [
    {
      "id": "fb_550e8400-e29b-41d4-a716-446655440000",
      "source": "website",
      "text": "Great product!",
      "customer_id": "customer_123",
      "created_at": "2024-01-15T10:30:00Z",
      "sentiment": 1,
      "sentiment_score": 0.85,
      "topic_cluster": "product_quality"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "has_next": true
}
```

### Get Single Feedback
Retrieve a specific feedback item with annotations.

```http
GET /api/feedback/{feedback_id}
```

**Response (200):**
```json
{
  "id": "fb_550e8400-e29b-41d4-a716-446655440000",
  "source": "website",
  "text": "Great product!",
  "customer_id": "customer_123",
  "created_at": "2024-01-15T10:30:00Z",
  "normalized_text": "great product",
  "detected_language": "en",
  "meta": {},
  "nlp_annotations": [
    {
      "id": 1,
      "sentiment": 1,
      "sentiment_score": 0.85,
      "topic_id": 5,
      "toxicity_score": 0.1
    }
  ]
}
```

### Search Feedback
Search feedback items by text content.

```http
GET /api/feedback/search?q=great+product&sentiment=1
```

**Query Parameters:**
- `q` (string, required): Search query
- `sentiment` (integer, optional): Filter by sentiment (-1, 0, 1)

**Response (200):**
```json
[
  {
    "id": "fb_550e8400-e29b-41d4-a716-446655440000",
    "text": "Great product!",
    "sentiment": 1,
    "score": 0.95
  }
]
```

---

## Topics Endpoints

### Get Topics
Retrieve all topics.

```http
GET /api/topics
```

**Response (200):**
```json
[
  {
    "id": 1,
    "label": "Product Quality",
    "keywords": ["quality", "product", "excellent"],
    "feedback_count": 45
  },
  {
    "id": 2,
    "label": "Customer Support",
    "keywords": ["support", "help", "service"],
    "feedback_count": 32
  }
]
```

### Get Single Topic
Retrieve a specific topic with statistics.

```http
GET /api/topics/{topic_id}
```

**Response (200):**
```json
{
  "id": 1,
  "label": "Product Quality",
  "keywords": ["quality", "product", "excellent"],
  "feedback_count": 45,
  "sentiment_distribution": {
    "positive": 35,
    "neutral": 8,
    "negative": 2
  },
  "avg_sentiment": 0.78
}
```

### Create Topic
Create a new topic.

```http
POST /api/topics
Content-Type: application/json

{
  "label": "New Topic",
  "keywords": ["new", "topic", "keywords"]
}
```

### Update Topic
Update an existing topic.

```http
PUT /api/topics/{topic_id}
Content-Type: application/json

{
  "label": "Updated Topic",
  "keywords": ["updated", "keywords"]
}
```

### Delete Topic
Delete a topic.

```http
DELETE /api/topics/{topic_id}
```

---

## Trends Endpoints

### Get Sentiment Trends
Retrieve sentiment trends over time.

```http
GET /api/trends/sentiment?group_by=day
```

**Query Parameters:**
- `group_by` (string, optional): Grouping period - "day", "week", "month" (default: "day")

**Response (200):**
```json
[
  {
    "period": "2024-01-15",
    "positive_count": 25,
    "negative_count": 8,
    "neutral_count": 12
  },
  {
    "period": "2024-01-16",
    "positive_count": 30,
    "negative_count": 5,
    "neutral_count": 15
  }
]
```

### Get Topic Distribution
Retrieve topic distribution with feedback counts.

```http
GET /api/trends/topics
```

**Response (200):**
```json
[
  {
    "id": 1,
    "label": "Product Quality",
    "feedback_count": 45,
    "percentage": 30.0
  },
  {
    "id": 2,
    "label": "Customer Support",
    "feedback_count": 32,
    "percentage": 21.3
  }
]
```

### Get Customer Statistics
Retrieve customer feedback statistics.

```http
GET /api/trends/customers
```

**Response (200):**
```json
[
  {
    "customer_id": "customer_123",
    "feedback_count": 5,
    "avg_sentiment": 0.7
  },
  {
    "customer_id": "customer_456",
    "feedback_count": 3,
    "avg_sentiment": 0.4
  }
]
```

---

## Query Endpoints

### Chat Query
Ask questions about the feedback data.

```http
POST /api/query/chat
Content-Type: application/json

{
  "query": "What are customers saying about our product quality?"
}
```

**Response (200):**
```json
{
  "response": "Based on the feedback analysis, customers generally have positive sentiments about product quality...",
  "sources": ["fb_123", "fb_456", "fb_789"],
  "confidence": 0.85,
  "timestamp": "2024-01-15T10:30:00.123456Z"
}
```

---

## Upload Endpoints

### Upload CSV
Upload feedback data from a CSV file.

```http
POST /api/upload/csv
Content-Type: multipart/form-data

file: feedback.csv
```

**CSV Format:**
```csv
source,text,customer_id,created_at
website,"Great product!",customer_123,2024-01-15T10:30:00Z
mobile_app,"Needs improvement",customer_456,2024-01-16T11:45:00Z
```

**Response (200):**
```json
{
  "processed_count": 150,
  "errors": [],
  "status": "completed"
}
```

### Upload JSONL
Upload feedback data from a JSONL file.

```http
POST /api/upload/jsonl
Content-Type: multipart/form-data

file: feedback.jsonl
```

**JSONL Format:**
```jsonl
{"source": "website", "text": "Great product!", "customer_id": "customer_123", "created_at": "2024-01-15T10:30:00Z"}
{"source": "mobile_app", "text": "Needs improvement", "customer_id": "customer_456", "created_at": "2024-01-16T11:45:00Z"}
```

---

## System Endpoints

### Health Check
Check service health.

```http
GET /health
```

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456Z",
  "version": "0.1.0"
}
```

### Kubernetes Health Check
Simple health check for Kubernetes.

```http
GET /healthz
```

**Response (200):**
```
ok
```

### Metrics (Development Only)
Prometheus metrics endpoint.

```http
GET /metrics
```

**Response (200):**
```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/feedback",status_code="200"} 42
...
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid parameters: Page must be >= 1"
}
```

### 404 Not Found
```json
{
  "detail": "Feedback item not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "text"],
      "msg": "Field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to process request: Database connection error"
}
```

---

## Rate Limiting

API requests are rate limited to 60 requests per minute per IP address. Exceeding this limit returns:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

---

## Data Types

### Sentiment Values
- `-1`: Negative sentiment
- `0`: Neutral sentiment
- `1`: Positive sentiment

### Source Types
- `website`: Website feedback
- `mobile_app`: Mobile application feedback
- `support_ticket`: Customer support tickets
- `survey`: Customer surveys
- `social_media`: Social media mentions
- `api`: Direct API submissions

### Date Format
All dates use ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`

---

## SDKs and Examples

### Python Client
```python
import requests

# Create feedback
response = requests.post("http://localhost:8000/api/feedback", json={
    "source": "api",
    "text": "Great product!",
    "customer_id": "customer_123"
})

# Get feedback list
response = requests.get("http://localhost:8000/api/feedback?page=1&page_size=10")
```

### cURL Examples
```bash
# Create feedback
curl -X POST http://localhost:8000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{"source": "website", "text": "Great product!"}'

# Get feedback with filtering
curl "http://localhost:8000/api/feedback?page=1&source=website"

# Upload CSV file
curl -X POST http://localhost:8000/api/upload/csv \
  -F "file=@feedback.csv"
```

---

## Changelog

### Version 0.1.0
- Initial API release
- Feedback CRUD operations
- Basic analytics endpoints
- File upload support
- Health checks and metrics
