"""
Prometheus metrics configuration and collection.
"""
import os
from typing import Optional
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from prometheus_client.registry import CollectorRegistry

from .logging import log


# Create registry for metrics
registry = CollectorRegistry()

# HTTP Request Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=registry,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
    registry=registry,
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    buckets=(100, 1000, 10000, 100000, 1000000),
    registry=registry,
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint", "status_code"],
    buckets=(100, 1000, 10000, 100000, 1000000),
    registry=registry,
)

# Application Metrics
active_connections = Gauge(
    "active_connections",
    "Number of active connections",
    registry=registry,
)

feedback_processed_total = Counter(
    "feedback_processed_total",
    "Total number of feedback items processed",
    ["source", "status"],
    registry=registry,
)

# Worker Metrics
worker_jobs_total = Counter(
    "worker_jobs_total",
    "Total number of worker jobs processed",
    ["job_type", "status"],
    registry=registry,
)

worker_job_duration_seconds = Histogram(
    "worker_job_duration_seconds",
    "Worker job duration in seconds",
    ["job_type"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
    registry=registry,
)

worker_active_jobs = Gauge(
    "worker_active_jobs",
    "Number of currently active worker jobs",
    ["job_type"],
    registry=registry,
)

# Service Health Metrics
service_health_status = Gauge(
    "service_health_status",
    "Service health status (1=healthy, 0=unhealthy)",
    ["service"],
    registry=registry,
)

# Database Metrics
db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
    registry=registry,
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.01, 0.1, 1.0, 5.0),
    registry=registry,
)

# Cache Metrics
cache_hits_total = Counter(
    "cache_hits_total",
    "Total number of cache hits",
    ["cache_name"],
    registry=registry,
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total number of cache misses",
    ["cache_name"],
    registry=registry,
)

cache_size = Gauge(
    "cache_size",
    "Current cache size",
    ["cache_name"],
    registry=registry,
)


def is_development_mode() -> bool:
    """Check if we're running in development mode."""
    return os.getenv("ENVIRONMENT", "development").lower() in ["dev", "development", "local"]


def get_metrics() -> bytes:
    """Generate latest metrics in Prometheus format."""
    try:
        return generate_latest(registry)
    except Exception as e:
        log.error("Failed to generate metrics", extra={"error": str(e)})
        return b"# Error generating metrics\n"


def increment_http_requests(method: str, endpoint: str, status_code: int):
    """Increment HTTP request counter."""
    try:
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
    except Exception as e:
        log.warning("Failed to increment HTTP request counter", extra={"error": str(e)})


def observe_http_request_duration(method: str, endpoint: str, duration: float):
    """Record HTTP request duration."""
    try:
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    except Exception as e:
        log.warning("Failed to record HTTP request duration", extra={"error": str(e)})


def observe_worker_job_duration(job_type: str, duration: float):
    """Record worker job duration."""
    try:
        worker_job_duration_seconds.labels(job_type=job_type).observe(duration)
    except Exception as e:
        log.warning("Failed to record worker job duration", extra={"error": str(e)})


def increment_worker_jobs(job_type: str, status: str = "success"):
    """Increment worker jobs counter."""
    try:
        worker_jobs_total.labels(job_type=job_type, status=status).inc()
    except Exception as e:
        log.warning("Failed to increment worker jobs counter", extra={"error": str(e)})


def set_service_health(service: str, healthy: bool):
    """Set service health status."""
    try:
        service_health_status.labels(service=service).set(1 if healthy else 0)
    except Exception as e:
        log.warning("Failed to set service health status", extra={"error": str(e)})


def increment_feedback_processed(source: str, status: str = "success"):
    """Increment feedback processed counter."""
    try:
        feedback_processed_total.labels(source=source, status=status).inc()
    except Exception as e:
        log.warning("Failed to increment feedback processed counter", extra={"error": str(e)})


def update_active_connections(count: int):
    """Update active connections gauge."""
    try:
        active_connections.set(count)
    except Exception as e:
        log.warning("Failed to update active connections", extra={"error": str(e)})


def observe_db_query_duration(operation: str, table: str, duration: float):
    """Record database query duration."""
    try:
        db_query_duration_seconds.labels(operation=operation, table=table).observe(duration)
    except Exception as e:
        log.warning("Failed to record database query duration", extra={"error": str(e)})


def increment_cache_hit(cache_name: str):
    """Increment cache hit counter."""
    try:
        cache_hits_total.labels(cache_name=cache_name).inc()
    except Exception as e:
        log.warning("Failed to increment cache hit counter", extra={"error": str(e)})


def increment_cache_miss(cache_name: str):
    """Increment cache miss counter."""
    try:
        cache_misses_total.labels(cache_name=cache_name).inc()
    except Exception as e:
        log.warning("Failed to increment cache miss counter", extra={"error": str(e)})


def set_cache_size(cache_name: str, size: int):
    """Set cache size gauge."""
    try:
        cache_size.labels(cache_name=cache_name).set(size)
    except Exception as e:
        log.warning("Failed to set cache size", extra={"error": str(e)})


# Initialize default metrics
def initialize_metrics():
    """Initialize default metric values."""
    try:
        # Set initial service health
        set_service_health("api", True)
        set_service_health("worker", True)
        set_service_health("database", True)

        # Set initial active connections
        update_active_connections(0)

        log.info("Metrics initialized successfully")
    except Exception as e:
        log.error("Failed to initialize metrics", extra={"error": str(e)})


# Initialize metrics on import
initialize_metrics()
