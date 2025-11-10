# API Reference

## Overview

The AI Customer Insights Agent provides a REST API for managing customer feedback, performing analytics, and interacting with the AI assistant. All endpoints return JSON responses and use standard HTTP status codes.

## Base URL
```
http://localhost:8001
```

## Authentication
The API supports JWT-based authentication for admin operations. Most read-only endpoints are publicly accessible, but admin functions require authentication.

## Content Types
- **Request**: `application/json`
- **Response**: `application/json`
- **File Upload**: `multipart/form-data`

---

## Router Structure

The API is organized into the following routers:

- `/api/*` - Legacy feedback and upload endpoints (via api_router)
- `/analytics/*` - Analytics and reporting endpoints
- `/chat/*` - AI chat and query endpoints
- `/admin/*` - Administrative operations (requires authentication)
- `/ingest/*` - Data ingestion endpoints
- `/api/export/*` - Data export endpoints
- `/metrics` - Prometheus metrics (development only)
- `/health*` - Health check endpoints

---

## Analytics Endpoints

### Get Sentiment Trends
Retrieve sentiment trends over time with caching.

```http
GET /analytics/sentiment-trends?group_by=day&start_date=2024-01-01&end_date=2024-12-31
```

**Query Parameters:**
- `group_by` (string, optional): Grouping period - "day", "week", "month" (default: "day")
- `start_date` (string, optional): Start date (YYYY-MM-DD)
- `end_date` (string, optional): End date (YYYY-MM-DD)

**Response (200):**
```json
[
  {
    "period": "2024-01-15",
    "positive_count": 25,
    "negative_count": 8,
    "neutral_count": 12
  }
]
```

### Get Volume Trends
Retrieve feedback volume trends over time.

```http
GET /analytics/volume-trends?group_by=day&start_date=2024-01-01&end_date=2024-12-31
```

**Query Parameters:**
- `group_by` (string, optional): Grouping period - "day", "week", "month" (default: "day")
- `start_date` (string, optional): Start date (YYYY-MM-DD)
- `end_date` (string, optional): End date (YYYY-MM-DD)

### Get Daily Aggregates
Retrieve paginated daily feedback aggregates.

```http
GET /analytics/daily-aggregates?page=1&page_size=30&start_date=2024-01-01&end_date=2024-12-31
```

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `page_size` (integer, optional): Days per page (default: 30, max: 365)
- `start_date` (string, optional): Start date (YYYY-MM-DD)
- `end_date` (string, optional): End date (YYYY-MM-DD)

### Get Customer Statistics
Retrieve customer feedback statistics.

```http
GET /analytics/customers?min_feedback_count=1&start_date=2024-01-01&end_date=2024-12-31
```

**Query Parameters:**
- `min_feedback_count` (integer, optional): Minimum feedback count per customer (default: 1)
- `start_date` (string, optional): Start date (YYYY-MM-DD)
- `end_date` (string, optional): End date (YYYY-MM-DD)

### Get Source Statistics
Retrieve feedback statistics by source.

```http
GET /analytics/sources?start_date=2024-01-01&end_date=2024-12-31
```

**Query Parameters:**
- `start_date` (string, optional): Start date (YYYY-MM-DD)
- `end_date` (string, optional): End date (YYYY-MM-DD)

### Get Toxicity Analysis
Retrieve toxicity analysis statistics.

```http
GET /analytics/toxicity?threshold=0.5&start_date=2024-01-01&end_date=2024-12-31
```

**Query Parameters:**
- `threshold` (float, optional): Toxicity threshold (0.0-1.0, default: 0.5)
- `start_date` (string, optional): Start date (YYYY-MM-DD)
- `end_date` (string, optional): End date (YYYY-MM-DD)

### Get Analytics Summary
Retrieve comprehensive analytics summary with caching.

```http
GET /analytics/summary?start=2024-01-01&end=2024-12-31
```

**Query Parameters:**
- `start` (string, optional): Start date (YYYY-MM-DD)
- `end` (string, optional): End date (YYYY-MM-DD)

**Response (200):**
```json
{
  "total_feedback": 150,
  "negative_percentage": 15.3,
  "daily_trend": [
    {
      "date": "2024-01-15",
      "positive_count": 25,
      "negative_count": 8,
      "neutral_count": 12
    }
  ]
}
```

### Get Analytics Topics
Retrieve analytics topics with caching.

```http
GET /analytics/topics?start=2024-01-01&end=2024-12-31
```

**Query Parameters:**
- `start` (string, optional): Start date (YYYY-MM-DD)
- `end` (string, optional): End date (YYYY-MM-DD)

### Get Feedback Examples
Retrieve sample feedback comments with optional filters.

```http
GET /analytics/examples?topic_id=1&sentiment=1&limit=10
```

**Query Parameters:**
- `topic_id` (integer, optional): Topic ID filter
- `sentiment` (integer, optional): Sentiment filter (-1, 0, 1)
- `limit` (integer, optional): Maximum examples (1-50, default: 10)

### Get Dashboard Summary
Retrieve dashboard summary statistics.

```http
GET /analytics/dashboard/summary?start_date=2024-01-01&end_date=2024-12-31
```

**Query Parameters:**
- `start_date` (string, optional): Start date (YYYY-MM-DD)
- `end_date` (string, optional): End date (YYYY-MM-DD)

**Response (200):**
```json
{
  "total_feedback": 150,
  "negative_percentage": 15.3,
  "topics_count": 8,
  "trends_14d": [
    {
      "date": "2024-01-15",
      "positive": 25,
      "negative": 8,
      "neutral": 12
    }
  ],
  "top_negative_topics": [
    {
      "name": "Customer Support",
      "count": 15,
      "negative_percentage": 45.2
    }
  ]
}
```

---

## Chat Endpoints

### Chat Query
Ask questions about feedback data using AI agent.

```http
POST /chat/chat/query
Content-Type: application/json

{
  "question": "What are customers saying about our product quality?",
  "filters": {
    "date_range": {
      "start_date": "2024-01-01",
      "end_date": "2024-12-31"
    },
    "sentiment": 1,
    "topic_ids": [1, 2],
    "source": "website",
    "customer_id": "customer_123",
    "language": "en"
  }
}
```

**Request Body:**
- `question` (string, required): The question to ask
- `filters` (object, optional): Optional filters to apply

**Response (200):**
```json
{
  "answer": "Based on the feedback analysis...",
  "citations": [
    {
      "feedback_id": "fb_550e8400-e29b-41d4-a716-446655440000",
      "topic_id": 1
    }
  ]
}
```

### Query (Legacy)
Legacy query endpoint for backward compatibility.

```http
POST /chat/query
Content-Type: application/json

{
  "query": "What are customers saying about support?",
  "context_limit": 10
}
```

### Get Conversation History
Retrieve conversation history.

```http
GET /chat/conversations
```

### Clarify Feedback
Get clarification about specific feedback.

```http
POST /chat/feedback/{feedback_id}/clarify
Content-Type: application/json

{
  "question": "Can you explain this feedback in more detail?"
}
```

### Clear Memory
Clear conversation memory.

```http
POST /chat/clear-memory
```

### Get Suggestions
Get query suggestions.

```http
GET /chat/suggestions
```

---

## Admin Endpoints (Requires Authentication)

### Login
Authenticate admin user.

```http
POST /admin/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

### Viewer Login
Authenticate viewer user.

```http
POST /admin/viewer/login
Content-Type: application/json

{
  "username": "viewer",
  "password": "password"
}
```

### Get System Stats
Retrieve comprehensive system statistics.

```http
GET /admin/stats
```

**Response (200):**
```json
{
  "database": {
    "size": "50 MB",
    "connection_string": "postgresql://user:***@host:5432/db"
  },
  "feedback": {
    "total": 150,
    "recent_24h": 25
  },
  "annotations": {
    "total": 150
  },
  "topics": {
    "total": 8
  }
}
```

### Refresh Materialized View
Refresh database materialized views.

```http
POST /admin/maintenance/refresh-materialized-view
```

### Database Health Check
Check database connectivity.

```http
GET /admin/health/database
```

**Response (200):**
```json
{
  "status": "healthy",
  "connection_time_ms": 5.2,
  "tables": ["feedback", "topic", "nlp_annotation"]
}
```

### Get Configuration
Retrieve system configuration (admin only).

```http
GET /admin/config
```

### Cleanup Old Data
Remove old feedback data.

```http
POST /admin/cleanup/old-data
Content-Type: application/json

{
  "days_old": 365,
  "dry_run": true
}
```

### Get Topics (Admin)
Retrieve topics for management.

```http
GET /admin/topics
```

### Get Topic Audit Log
Get audit log for topic changes.

```http
GET /admin/topic-audit/{topic_id}
```

### Get All Topic Audits
Get all topic audit logs.

```http
GET /admin/topic-audit?page=1&page_size=50
```

### Relabel Topic
Update topic label and keywords.

```http
POST /admin/relabel-topic
Content-Type: application/json

{
  "topic_id": 1,
  "new_label": "Updated Topic Name",
  "new_keywords": ["new", "keywords", "here"]
}
```

### Reassign Feedback
Reassign feedback to different topics.

```http
POST /admin/reassign-feedback
Content-Type: application/json

{
  "feedback_ids": ["fb_123", "fb_456"],
  "target_topic_id": 2
}
```

### Get Topic Feedback
Get feedback assigned to a topic.

```http
GET /admin/topics/{topic_id}/feedback?page=1&page_size=50
```

### Get Viewer Stats
Get statistics for viewer dashboard.

```http
GET /admin/viewer/stats
```

### Get Viewer Dashboard
Get dashboard data for viewers.

```http
GET /admin/viewer/dashboard
```

### Get Viewer Profile
Get viewer profile information.

```http
GET /admin/viewer/profile
```

---

## Ingestion Endpoints

### Create Feedback
Create a single feedback item.

```http
POST /ingest/feedback
Content-Type: application/x-www-form-urlencoded

source=website&text=Great product!&customer_id=customer_123
```

**Response (200):**
```json
{
  "id": "fb_550e8400-e29b-41d4-a716-446655440000",
  "source": "website",
  "text": "Great product!",
  "customer_id": "customer_123",
  "created_at": "2024-01-15T10:30:00.000000Z"
}
```

### Create Feedback Batch
Create multiple feedback items.

```http
POST /ingest/feedback/batch
Content-Type: application/json

[
  {
    "source": "website",
    "text": "Great product!",
    "customer_id": "customer_123"
  },
  {
    "source": "mobile",
    "text": "Could be better",
    "customer_id": "customer_456"
  }
]
```

**Response (200):**
```json
{
  "created": [
    {
      "id": "fb_123",
      "created_at": "2024-01-15T10:30:00.000000Z"
    }
  ],
  "count": 2
}
```

### Upload CSV
Upload feedback from CSV file.

```http
POST /ingest/upload/csv
Content-Type: multipart/form-data

file: feedback.csv&source=csv_upload
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
  "batch_id": "batch_550e8400-e29b-41d4-a716-446655440000",
  "processed_count": 150,
  "created_count": 145,
  "duplicate_count": 5,
  "error_count": 0,
  "skipped_non_english_count": 2,
  "job_id": "job_123"
}
```

### Upload JSONL
Upload feedback from JSONL file.

```http
POST /ingest/upload/json
Content-Type: multipart/form-data

file: feedback.jsonl
```

**JSONL Format:**
```jsonl
{"source": "website", "text": "Great product!", "customer_id": "customer_123", "created_at": "2024-01-15T10:30:00Z"}
{"source": "mobile_app", "text": "Needs improvement", "customer_id": "customer_456", "created_at": "2024-01-16T11:45:00Z"}
```

---

## Legacy API Endpoints

### Feedback Endpoints (via /api/feedback)
Standard CRUD operations for feedback items.

```http
GET /api/feedback?page=1&page_size=50&source=website&start_date=2024-01-01&end_date=2024-12-31
POST /api/feedback
GET /api/feedback/{feedback_id}
GET /api/feedback/search?q=query&sentiment=1
```

### Topics Endpoints (via /api/topics)
Topic management operations.

```http
GET /api/topics
GET /api/topics/{topic_id}
POST /api/topics
PUT /api/topics/{topic_id}
DELETE /api/topics/{topic_id}
```

### Upload Endpoints (via /api/upload)
File upload operations.

```http
POST /api/upload/csv
POST /api/upload/jsonl
```

### Query Endpoints (via /api/query)
Legacy query operations.

```http
POST /api/query/chat
```

---

## Export Endpoints

### Export Feedback CSV
Export feedback data as CSV with filters.

```http
GET /api/export/export.csv?source=website&start_date=2024-01-01&end_date=2024-12-31&sentiment_min=0.5
```

**Query Parameters:**
- `source` (string, optional): Filter by source
- `customer_id` (string, optional): Filter by customer ID
- `start_date` (string, optional): Start date (YYYY-MM-DD)
- `end_date` (string, optional): End date (YYYY-MM-DD)
- `sentiment_min` (float, optional): Minimum sentiment score
- `sentiment_max` (float, optional): Maximum sentiment score

### Export Topics CSV
Export topics data as CSV.

```http
GET /api/export/export/topics.csv?min_feedback_count=1
```

**Query Parameters:**
- `min_feedback_count` (integer, optional): Minimum feedback count (default: 1)

### Export Analytics CSV
Export daily analytics aggregates as CSV.

```http
GET /api/export/export/analytics.csv?start_date=2024-01-01&end_date=2024-12-31
```

**Query Parameters:**
- `start_date` (string, optional): Start date (YYYY-MM-DD)
- `end_date` (string, optional): End date (YYYY-MM-DD)

---

## System Endpoints

### Health Check
Basic health check.

```http
GET /health
```

**Response (200):**
```json
{
  "status": "healthy"
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

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid parameters: Page must be >= 1"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 413 Payload Too Large
```json
{
  "detail": "Question too long. 1500 characters exceeds limit of 1000"
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

### 429 Too Many Requests
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to process request: Database connection error"
}
```

---

## Authentication

### JWT Token Usage
Include the JWT token in the Authorization header:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Admin vs Viewer Roles
- **Admin**: Full access to all endpoints including topic management and system maintenance
- **Viewer**: Read-only access to analytics, dashboard, and basic statistics

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
- `csv_upload`: CSV file uploads

### Date Format
All dates use ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`

---

## SDKs and Examples

### Python Client
```python
import requests

# Create feedback
response = requests.post("http://localhost:8001/ingest/feedback",
    data={
        "source": "api",
        "text": "Great product!",
        "customer_id": "customer_123"
    }
)

# Get analytics summary
response = requests.get("http://localhost:8001/analytics/summary")

# Chat query
response = requests.post("http://localhost:8001/chat/chat/query", json={
    "question": "What are customers saying about support?"
})
```

### cURL Examples
```bash
# Create feedback
curl -X POST http://localhost:8001/ingest/feedback \
  -d "source=website&text=Great product!"

# Get analytics
curl http://localhost:8001/analytics/summary

# Chat query with auth
curl -X POST http://localhost:8001/chat/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How is customer satisfaction trending?"}'

# Export data
curl -o feedback.csv "http://localhost:8001/api/export/export.csv"

# Admin login
curl -X POST http://localhost:8001/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

---

## Rate Limiting

API requests are rate limited to prevent abuse:
- **General endpoints**: 60 requests per minute per IP
- **Analytics endpoints**: 30 requests per minute per IP
- **Admin endpoints**: 10 requests per minute per authenticated user
- **File uploads**: 5 uploads per minute per IP

---

## Caching

Analytics endpoints use Redis caching for improved performance:
- **Cache duration**: 5 minutes for most analytics endpoints
- **Cache keys**: Based on request parameters
- **Cache clearing**: Available via `/admin/cache/clear` endpoint

---

## Changelog

### Version 0.2.0
- **New Router Structure**: Organized endpoints into `/analytics`, `/chat`, `/admin`, `/ingest` routers
- **JWT Authentication**: Added authentication for admin operations
- **AI Chat Integration**: Advanced chat queries with LangChain agent
- **Analytics Caching**: Redis-based caching for performance
- **Advanced Analytics**: Toxicity analysis, customer stats, volume trends
- **Admin Panel**: Topic management, audit logs, system maintenance
- **Export API**: CSV export with filtering and streaming
- **Dashboard Summary**: Comprehensive dashboard statistics endpoint

### Version 0.1.0
- Initial API release
- Feedback CRUD operations
- Basic analytics endpoints
- File upload support
- Health checks and metrics
