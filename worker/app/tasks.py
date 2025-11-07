import os
import sys
import uuid
import time
from datetime import datetime

# Add server path to sys.path so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), '../../server'))

from app.models.feedback import FeedbackItem
from app.services.database import SessionLocal, create_tables
from app.services.sentiment_service import SentimentService
from app.services.clustering_service import ClusteringService
from app.logging import setup_logging, LoggingSettings, get_logger
from app.metrics import (
    increment_worker_jobs,
    observe_worker_job_duration,
    worker_active_jobs,
    increment_feedback_processed,
    set_service_health,
)

def process_feedback_batch(feedback_data: list):
    """Process a batch of feedback items: analyze sentiment and cluster topics"""

    # Setup logging for worker
    setup_logging(LoggingSettings())
    log = get_logger("worker")

    # Start job timing and metrics
    job_id = str(uuid.uuid4())
    job_start_time = time.time()
    batch_size = len(feedback_data)

    log.info(
        "Starting feedback batch processing",
        extra={
            "job_id": job_id,
            "batch_size": batch_size,
            "job_type": "feedback_batch_processing"
        }
    )

    # Increment active jobs metric
    worker_active_jobs.labels(job_type="feedback_batch").inc()

    # Initialize services
    sentiment_service = SentimentService()
    clustering_service = ClusteringService()

    # Create tables if they don't exist
    create_tables()

    db = SessionLocal()
    try:
        # Extract texts for batch processing
        texts = [item['text'] for item in feedback_data]

        # Analyze sentiment in batch
        log.info(
            "Analyzing sentiment for feedback batch",
            extra={
                "job_id": job_id,
                "batch_size": batch_size,
                "operation": "sentiment_analysis"
            }
        )
        sentiment_start = time.time()
        sentiment_results = sentiment_service.analyze_batch(texts)
        sentiment_duration = time.time() - sentiment_start

        log.info(
            "Sentiment analysis completed",
            extra={
                "job_id": job_id,
                "duration_seconds": round(sentiment_duration, 2),
                "texts_processed": len(texts)
            }
        )

        # Assign sentiment to feedback data
        for i, (sentiment, score) in enumerate(sentiment_results):
            feedback_data[i]['sentiment'] = sentiment
            feedback_data[i]['sentiment_score'] = score

        # Cluster topics
        log.info(
            "Starting topic clustering",
            extra={
                "job_id": job_id,
                "operation": "topic_clustering"
            }
        )
        clustering_start = time.time()
        cluster_assignments = clustering_service.cluster_texts(texts)
        clustering_duration = time.time() - clustering_start

        log.info(
            "Topic clustering completed",
            extra={
                "job_id": job_id,
                "duration_seconds": round(clustering_duration, 2),
                "clusters_found": len(cluster_assignments)
            }
        )

        # Assign cluster labels
        for cluster_name, indices in cluster_assignments.items():
            for idx in indices:
                feedback_data[idx]['topic_cluster'] = cluster_name

        # Save to database
        log.info(
            "Saving feedback items to database",
            extra={
                "job_id": job_id,
                "operation": "database_save",
                "items_to_save": len(feedback_data)
            }
        )
        db_start = time.time()
        for item in feedback_data:
            feedback_item = FeedbackItem(
                id=item.get('id', str(uuid.uuid4())),
                text=item['text'],
                sentiment=item['sentiment'],
                sentiment_score=item['sentiment_score'],
                topic_cluster=item['topic_cluster'],
                source=item.get('source', 'api'),
                created_at=item.get('created_at', datetime.utcnow())
            )
            db.add(feedback_item)

        db.commit()
        db_duration = time.time() - db_start

        # Calculate total job duration
        total_duration = time.time() - job_start_time

        # Update metrics
        increment_worker_jobs("feedback_batch", "success")
        observe_worker_job_duration("feedback_batch", total_duration)
        set_service_health("worker", True)

        # Increment feedback processed metrics
        for item in feedback_data:
            increment_feedback_processed(item.get('source', 'api'), "success")

        log.info(
            "Feedback batch processing completed successfully",
            extra={
                "job_id": job_id,
                "batch_size": batch_size,
                "total_duration_seconds": round(total_duration, 2),
                "sentiment_duration_seconds": round(sentiment_duration, 2),
                "clustering_duration_seconds": round(clustering_duration, 2),
                "database_duration_seconds": round(db_duration, 2),
                "status": "completed"
            }
        )

        return {
            "processed_count": len(feedback_data),
            "status": "completed",
            "job_id": job_id,
            "duration_seconds": round(total_duration, 2)
        }

    except Exception as e:
        # Calculate duration even for failed jobs
        total_duration = time.time() - job_start_time

        # Update metrics for failed job
        increment_worker_jobs("feedback_batch", "failed")
        observe_worker_job_duration("feedback_batch", total_duration)
        set_service_health("worker", False)

        log.error(
            "Feedback batch processing failed",
            extra={
                "job_id": job_id,
                "batch_size": batch_size,
                "duration_seconds": round(total_duration, 2),
                "error": str(e),
                "error_type": type(e).__name__,
                "status": "failed"
            }
        )

        db.rollback()
        raise e
    finally:
        db.close()
        # Decrement active jobs metric
        worker_active_jobs.labels(job_type="feedback_batch").dec()
