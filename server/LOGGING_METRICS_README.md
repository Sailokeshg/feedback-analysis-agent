# Logging and Metrics Integration

This document describes the structured logging and Prometheus metrics integration for the feedback analysis agent.

## Features

- **Structured JSON Logging**: Using loguru for consistent, structured logs with request tracing
- **Request Timing Middleware**: Automatic request timing with request ID generation
- **Prometheus Metrics**: Comprehensive metrics collection with /metrics endpoint
- **Worker Job Monitoring**: Detailed worker job duration histograms

## Structured Logging

### Configuration

Logging is configured in `app/logging.py` with the following features:

- **JSON Format**: All logs are output in structured JSON format
- **Request Context**: Automatic inclusion of `request_id`, `user_id`, and `correlation_id`
- **Log Levels**: Configurable via `LOG_LEVEL` environment variable
- **File Rotation**: Automatic log rotation and retention

### Log Format

```json
{
  "timestamp": "2024-01-15T10:30:00.123456Z",
  "level": "INFO",
  "message": "Request started",
  "logger": "app",
  "module": "middleware.request_timing",
  "function": "RequestTimingMiddleware.__call__",
  "line": 45,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "GET",
  "url": "http://localhost:8000/api/feedback",
  "client_ip": "192.168.1.100"
}
```

### Environment Variables

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR) - default: INFO
- `LOG_JSON_LOGS`: Enable JSON format (true/false) - default: true
- `LOG_FILE`: Log file path - default: logs/app.log
- `LOG_ROTATION`: Log rotation size - default: 10 MB
- `LOG_RETENTION`: Log retention period - default: 1 week

## Request Timing Middleware

### Features

- **Request ID Generation**: Unique UUID for each request
- **Timing Measurement**: Precise request duration tracking
- **Context Propagation**: Request ID available throughout request lifecycle
- **Structured Logging**: Request details included in logs

### Middleware Order

The middleware is added in this order (important for correct operation):

1. `RequestTimingMiddleware` - Must be first to capture request start
2. CORS middleware
3. Rate limiting middleware
4. Other middleware

### Request Context

The middleware automatically provides:

- `request_id`: Unique identifier for request tracing
- Request timing information
- Client IP extraction
- User agent logging

## Prometheus Metrics

### Metrics Collected

#### HTTP Metrics
- `http_requests_total{method, endpoint, status_code}` - Total HTTP requests
- `http_request_duration_seconds{method, endpoint}` - Request duration histogram
- `http_request_size_bytes{method, endpoint}` - Request size histogram
- `http_response_size_bytes{method, endpoint, status_code}` - Response size histogram

#### Application Metrics
- `feedback_processed_total{source, status}` - Feedback processing counter
- `active_connections` - Current active connections
- `service_health_status{service}` - Service health (1=healthy, 0=unhealthy)

#### Worker Metrics
- `worker_jobs_total{job_type, status}` - Worker jobs counter
- `worker_job_duration_seconds{job_type}` - Worker job duration histogram
- `worker_active_jobs{job_type}` - Currently active worker jobs

#### Database Metrics
- `db_connections_active` - Active database connections
- `db_query_duration_seconds{operation, table}` - Database query duration

#### Cache Metrics
- `cache_hits_total{cache_name}` - Cache hits
- `cache_misses_total{cache_name}` - Cache misses
- `cache_size{cache_name}` - Current cache size

### Metrics Endpoint

**URL**: `/metrics`
**Method**: GET
**Format**: Prometheus text-based format
**Availability**: Development mode only (ENVIRONMENT=development/dev/local)

Example metrics output:
```prometheus
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/feedback",status_code="200"} 42
http_requests_total{method="POST",endpoint="/api/feedback",status_code="201"} 15

# HELP worker_job_duration_seconds Worker job duration in seconds
# TYPE worker_job_duration_seconds histogram
worker_job_duration_seconds_bucket{job_type="feedback_batch",le="1.0"} 0
worker_job_duration_seconds_bucket{job_type="feedback_batch",le="5.0"} 2
worker_job_duration_seconds_bucket{job_type="feedback_batch",le="10.0"} 8
worker_job_duration_seconds_bucket{job_type="feedback_batch",le="30.0"} 15
worker_job_duration_seconds_bucket{job_type="feedback_batch",le="60.0"} 22
worker_job_duration_seconds_bucket{job_type="feedback_batch",le="120.0"} 28
worker_job_duration_seconds_bucket{job_type="feedback_batch",le="300.0"} 30
worker_job_duration_seconds_bucket{job_type="feedback_batch",le="600.0"} 30
worker_job_duration_seconds_bucket{job_type="feedback_batch",le="+Inf"} 30
worker_job_duration_seconds_count{job_type="feedback_batch"} 30
worker_job_duration_seconds_sum{job_type="feedback_batch"} 1250.5
```

## Worker Job Monitoring

### Job Duration Histogram

The worker tracks job duration with the following buckets:
- 1s, 5s, 10s, 30s, 60s, 120s, 300s, 600s

### Structured Logging

Worker jobs include detailed logging:
```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "level": "INFO",
  "message": "Feedback batch processing completed successfully",
  "logger": "worker",
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "batch_size": 50,
  "total_duration_seconds": 45.6,
  "sentiment_duration_seconds": 12.3,
  "clustering_duration_seconds": 25.4,
  "database_duration_seconds": 7.9,
  "status": "completed"
}
```

### Metrics Integration

Worker jobs automatically update:
- `worker_jobs_total` counter
- `worker_job_duration_seconds` histogram
- `worker_active_jobs` gauge
- `service_health_status` gauge

## Usage Examples

### In Application Code

```python
from app.logging import get_logger
from app.metrics import increment_http_requests, observe_http_request_duration

log = get_logger("my_module")

def my_endpoint():
    log.info("Processing request", extra={"user_id": "123"})
    # ... processing ...
    log.info("Request completed")
```

### In Worker Tasks

```python
import time
from app.logging import get_logger
from app.metrics import observe_worker_job_duration, increment_worker_jobs

log = get_logger("worker_task")

def process_data():
    start_time = time.time()
    job_id = "unique-job-id"

    log.info("Starting data processing", extra={"job_id": job_id})

    try:
        # ... processing logic ...
        duration = time.time() - start_time

        observe_worker_job_duration("data_processing", duration)
        increment_worker_jobs("data_processing", "success")

        log.info("Data processing completed", extra={
            "job_id": job_id,
            "duration_seconds": duration,
            "status": "success"
        })

    except Exception as e:
        duration = time.time() - start_time
        observe_worker_job_duration("data_processing", duration)
        increment_worker_jobs("data_processing", "failed")

        log.error("Data processing failed", extra={
            "job_id": job_id,
            "duration_seconds": duration,
            "error": str(e),
            "status": "failed"
        })
```

## Development vs Production

### Development Mode
- `/metrics` endpoint available
- Console logging enabled
- File logging enabled
- More verbose logging

### Production Mode
- `/metrics` endpoint disabled
- File logging only
- Optimized performance
- Less verbose logging

## Testing

Run the integration test:

```bash
cd server
python test_logging_metrics.py
```

This verifies:
- Structured logging configuration
- Metrics collection
- Development mode detection
- Worker job duration histogram
