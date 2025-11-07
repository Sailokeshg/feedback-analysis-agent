#!/usr/bin/env python3
"""
Demonstration script showing logging and metrics integration.
"""
import os
import sys
import time
import json
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.logging import setup_logging, LoggingSettings, get_logger, set_request_context
from app.metrics import (
    increment_http_requests,
    observe_http_request_duration,
    increment_worker_jobs,
    observe_worker_job_duration,
    get_metrics,
    increment_feedback_processed,
    set_service_health,
)


def demo_request_logging():
    """Demonstrate request logging with context."""
    print("\n📝 Demonstrating Request Logging")
    print("=" * 50)

    # Setup logging
    setup_logging(LoggingSettings(json_logs=True))

    # Simulate a request
    request_id = "demo-request-12345"
    set_request_context(request_id=request_id)

    log = get_logger("demo")

    # Log request start
    log.info("Request started", extra={
        "method": "GET",
        "url": "/api/feedback",
        "client_ip": "192.168.1.100",
        "user_agent": "DemoClient/1.0"
    })

    # Simulate processing
    time.sleep(0.1)

    # Log request completion with metrics
    duration = 0.123
    observe_http_request_duration("GET", "/api/feedback", duration)
    increment_http_requests("GET", "/api/feedback", 200)

    log.info("Request completed", extra={
        "status_code": 200,
        "duration_ms": round(duration * 1000, 2),
        "response_size_bytes": 1024
    })

    print("✓ Request logging with context completed")


def demo_worker_job_logging():
    """Demonstrate worker job logging and metrics."""
    print("\n⚙️ Demonstrating Worker Job Logging")
    print("=" * 50)

    log = get_logger("worker_demo")
    job_id = "worker-job-demo-67890"

    # Log job start
    log.info("Starting feedback batch processing", extra={
        "job_id": job_id,
        "batch_size": 25,
        "job_type": "feedback_batch_processing"
    })

    start_time = time.time()

    # Simulate job phases
    time.sleep(0.05)  # Sentiment analysis
    log.info("Sentiment analysis completed", extra={
        "job_id": job_id,
        "texts_processed": 25,
        "duration_seconds": 0.05
    })

    time.sleep(0.08)  # Clustering
    log.info("Topic clustering completed", extra={
        "job_id": job_id,
        "clusters_found": 5,
        "duration_seconds": 0.08
    })

    time.sleep(0.03)  # Database save
    log.info("Database save completed", extra={
        "job_id": job_id,
        "items_saved": 25,
        "duration_seconds": 0.03
    })

    # Calculate total duration
    total_duration = time.time() - start_time

    # Update metrics
    observe_worker_job_duration("feedback_batch", total_duration)
    increment_worker_jobs("feedback_batch", "success")
    increment_feedback_processed("api", "success")
    set_service_health("worker", True)

    # Log job completion
    log.info("Feedback batch processing completed successfully", extra={
        "job_id": job_id,
        "batch_size": 25,
        "total_duration_seconds": round(total_duration, 2),
        "sentiment_duration_seconds": 0.05,
        "clustering_duration_seconds": 0.08,
        "database_duration_seconds": 0.03,
        "status": "completed"
    })

    print("✓ Worker job logging and metrics completed")


def demo_metrics_output():
    """Demonstrate metrics output."""
    print("\n📊 Demonstrating Metrics Output")
    print("=" * 50)

    # Add some more metrics
    increment_http_requests("POST", "/api/feedback", 201)
    increment_http_requests("GET", "/api/topics", 200)
    observe_http_request_duration("POST", "/api/feedback", 0.234)

    increment_worker_jobs("topic_analysis", "success")
    observe_worker_job_duration("topic_analysis", 15.7)

    # Get metrics
    metrics_data = get_metrics()
    metrics_text = metrics_data.decode('utf-8')

    # Count different metric types
    lines = metrics_text.splitlines()
    counters = sum(1 for line in lines if line.startswith('# TYPE') and 'counter' in line)
    histograms = sum(1 for line in lines if line.startswith('# TYPE') and 'histogram' in line)
    gauges = sum(1 for line in lines if line.startswith('# TYPE') and 'gauge' in line)

    print(f"📈 Metrics Summary:")
    print(f"   • Total metric lines: {len(lines)}")
    print(f"   • Counter metrics: {counters}")
    print(f"   • Histogram metrics: {histograms}")
    print(f"   • Gauge metrics: {gauges}")

    print("\n📋 Sample Metrics Output:")
    print("-" * 30)

    # Show a few example metrics
    sample_lines = []
    in_sample = False
    for line in lines:
        if line.startswith('# HELP http_requests_total'):
            in_sample = True
        if in_sample and len(sample_lines) < 10:
            sample_lines.append(line)
        if in_sample and line.startswith('# HELP') and 'http_requests_total' not in line:
            break

    for line in sample_lines:
        print(f"   {line}")

    print("   ... (truncated)")
    print("✓ Metrics output demonstration completed")


def demo_error_logging():
    """Demonstrate error logging."""
    print("\n🚨 Demonstrating Error Logging")
    print("=" * 50)

    log = get_logger("error_demo")

    try:
        # Simulate an error
        raise ValueError("Demo error for logging")
    except Exception as e:
        log.error("An error occurred during processing", extra={
            "error": str(e),
            "error_type": type(e).__name__,
            "operation": "demo_processing",
            "severity": "high"
        })

        # Update error metrics
        increment_http_requests("GET", "/api/failed", 500)
        set_service_health("api", False)

    print("✓ Error logging demonstration completed")


def main():
    """Run all demonstrations."""
    print("🚀 Logging and Metrics Integration Demo")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Log level: {os.getenv('LOG_LEVEL', 'INFO')}")

    try:
        demo_request_logging()
        demo_worker_job_logging()
        demo_metrics_output()
        demo_error_logging()

        print("\n" + "=" * 60)
        print("✅ All demonstrations completed successfully!")
        print("\n🎯 Key Features Demonstrated:")
        print("   • Structured JSON logging with request_id")
        print("   • Request timing and context propagation")
        print("   • Worker job duration histogram")
        print("   • Prometheus metrics collection")
        print("   • Error handling and logging")
        print("   • Service health monitoring")

        print(f"\nFinished at: {datetime.now().isoformat()}")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
