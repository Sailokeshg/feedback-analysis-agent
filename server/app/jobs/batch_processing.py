"""
RQ jobs for batch processing of feedback data.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from ..services.database import SessionLocal
from ..repositories import FeedbackRepository

logger = logging.getLogger(__name__)

def process_feedback_batch(
    feedback_ids: List[str],
    batch_id: str,
    source: str = "batch_ingest"
) -> Dict[str, Any]:
    """
    RQ job to process a batch of feedback items.
    This job handles NLP analysis, topic classification, and other processing tasks.

    Args:
        feedback_ids: List of feedback UUIDs to process
        batch_id: Unique identifier for this batch
        source: Source identifier for logging

    Returns:
        Processing results summary
    """
    logger.info(f"Starting batch processing for batch {batch_id} with {len(feedback_ids)} items")

    db = SessionLocal()
    try:
        repo = FeedbackRepository(db)

        processed = []
        failed = []

        for feedback_id in feedback_ids:
            try:
                # Get feedback item
                feedback = repo.get_feedback_by_id(feedback_id)
                if not feedback:
                    failed.append({
                        "id": feedback_id,
                        "error": "Feedback not found"
                    })
                    continue

                # TODO: Add actual NLP processing here
                # For now, just mark as processed with basic analysis

                # Example: Basic sentiment analysis placeholder
                # In production, this would call ML models
                sentiment_score = 0.0  # Placeholder
                sentiment = 0  # Neutral placeholder

                # Add NLP annotation
                annotation = repo.add_nlp_annotation(
                    feedback_id=feedback.id,
                    sentiment=sentiment,
                    sentiment_score=sentiment_score,
                    topic_id=None,  # Would be determined by ML model
                    toxicity_score=0.0  # Placeholder
                )

                processed.append({
                    "id": str(feedback.id),
                    "sentiment": sentiment,
                    "sentiment_score": sentiment_score
                })

            except Exception as e:
                logger.error(f"Failed to process feedback {feedback_id}: {e}")
                failed.append({
                    "id": feedback_id,
                    "error": str(e)
                })

        result = {
            "batch_id": batch_id,
            "source": source,
            "processed_count": len(processed),
            "failed_count": len(failed),
            "processed": processed,
            "failed": failed,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"Completed batch processing for batch {batch_id}: {len(processed)} processed, {len(failed)} failed")
        return result

    except Exception as e:
        logger.error(f"Batch processing failed for batch {batch_id}: {e}")
        raise
    finally:
        db.close()

def enqueue_feedback_batch_processing(
    feedback_ids: List[str],
    batch_id: str,
    source: str = "batch_ingest"
) -> str:
    """
    Helper function to enqueue batch processing job.

    Returns the job ID for tracking.
    """
    try:
        from rq import Queue
        from redis import Redis

        # Connect to Redis (would be configured from settings)
        redis_conn = Redis(host='localhost', port=6379, db=0)
        queue = Queue('feedback_processing', connection=redis_conn)

        # Enqueue the job
        job = queue.enqueue(
            process_feedback_batch,
            feedback_ids,
            batch_id,
            source,
            job_timeout=3600,  # 1 hour timeout
            result_ttl=86400   # Keep results for 24 hours
        )

        logger.info(f"Enqueued batch processing job {job.id} for batch {batch_id}")
        return job.id

    except ImportError:
        logger.warning("RQ not available, skipping job enqueue")
        return "mock-job-id"
    except Exception as e:
        logger.error(f"Failed to enqueue batch processing job: {e}")
        raise
