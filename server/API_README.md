# AI Customer Insights Agent API

FastAPI-based API for processing and analyzing customer feedback with comprehensive analytics, ingestion, and administrative capabilities.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -e .[dev]

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📋 API Structure

### Router Groups

#### `/ingest` - Data Ingestion
- `POST /ingest/feedback` - Create single feedback item
- `POST /ingest/feedback/batch` - Create multiple feedback items
- `POST /ingest/upload/csv` - Upload CSV file
- `POST /ingest/upload/json` - Upload JSON file

#### `/analytics` - Data Analytics & Reporting
- `GET /analytics/sentiment-trends` - Sentiment trends over time
- `GET /analytics/volume-trends` - Feedback volume trends
- `GET /analytics/daily-aggregates` - Daily statistics
- `GET /analytics/topics` - Topic distribution
- `GET /analytics/customers` - Customer statistics
- `GET /analytics/sources` - Source statistics
- `GET /analytics/toxicity` - Toxicity analysis
- `GET /analytics/dashboard/summary` - Dashboard summary

#### `/chat` - Conversational Interface
- `POST /chat/query` - Natural language queries
- `GET /chat/conversations` - Conversation history
- `POST /chat/feedback/{id}/clarify` - Clarify specific feedback
- `GET /chat/suggestions` - Query suggestions

#### `/admin` - Administrative Operations
- `GET /admin/stats` - System statistics
- `POST /admin/maintenance/refresh-materialized-view` - Refresh analytics view
- `GET /admin/health/database` - Database health check
- `GET /admin/config` - Configuration info
- `POST /admin/cleanup/old-data` - Data cleanup
- `GET /admin/logs/recent` - Recent logs
- `POST /admin/cache/clear` - Clear caches

## 🔧 Configuration

### Environment Variables

```bash
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/feedback_db

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# CORS
CORS_ALLOW_ORIGINS=["http://localhost:3000"]

# External Services
EXTERNAL_CHROMA_URL=http://localhost:8000
EXTERNAL_REDIS_URL=redis://localhost:6379
```

### Pydantic Settings

The application uses Pydantic settings for type-safe configuration:

- **DatabaseSettings**: Connection pool, URL configuration
- **APISettings**: Host, port, docs URLs, debug mode
- **CORSSettings**: Origin policies, credentials, headers
- **RateLimitSettings**: Request limits, burst capacity
- **SecuritySettings**: JWT secrets, expiration times
- **ExternalServicesSettings**: Chroma, Redis URLs

## 🛡️ Security Features

### Rate Limiting
- **In-memory token bucket algorithm**
- **60 requests per minute** default limit
- **10 burst capacity** for traffic spikes
- **X-RateLimit-* headers** for client awareness
- **429 status code** with retry information

### CORS Protection
- **Configurable origins** whitelist
- **Credentials support** for authenticated requests
- **Method and header** restrictions

### Input Validation
- **Pydantic models** for all request/response data
- **Type hints** and automatic validation
- **SQL injection prevention** via parameterized queries

## 📊 Health Checks

### `/health` - Application Health
Returns JSON status information:
```json
{
  "status": "healthy"
}
```

### `/healthz` - Kubernetes Health Check
Returns plain text "ok" for load balancer health checks.

## 📖 API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

### Documentation Features
- **Interactive testing** of all endpoints
- **Request/response examples**
- **Parameter descriptions** and validation
- **Error response schemas**

## 🔍 Query Parameters

### Common Parameters
- `start_date`: Filter from date (YYYY-MM-DD)
- `end_date`: Filter to date (YYYY-MM-DD)
- `page`: Page number (≥1)
- `page_size`: Items per page (1-1000)

### Analytics Parameters
- `group_by`: Time grouping (day/week/month)
- `min_feedback_count`: Minimum count threshold
- `threshold`: Toxicity/confidence threshold (0.0-1.0)

## 📤 Response Formats

### Paginated Responses
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "has_next": true
}
```

### Error Responses
```json
{
  "detail": "Error message description"
}
```

## 🗄️ Database Integration

### Connection Pooling
- **Pool size**: 10 connections
- **Max overflow**: 20 additional connections
- **Pre-ping**: Automatic reconnection on connection loss

### Repository Pattern
- **Parameterized queries** for security
- **Retry/backoff** for transient failures
- **Read-only analytics** with whitelisted operations
- **Pagination helpers** with date filtering

## 🚀 Production Deployment

### Environment Setup
1. Set environment variables
2. Configure database connection
3. Enable rate limiting
4. Set CORS origins for frontend

### Monitoring
- Health check endpoints for load balancers
- Structured logging integration
- Performance monitoring hooks

### Scaling Considerations
- Database connection pooling
- Rate limiting per client IP
- Materialized view refreshing
- Cache management for analytics
