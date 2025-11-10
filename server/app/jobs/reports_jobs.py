"""
Reports queue jobs for analytics and reporting generation.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from ..services.database import SessionLocal
from ..services.cache_service import cache_service
from ..repositories import FeedbackRepository, AnalyticsRepository
from ..services.queue_service import queue_service

logger = logging.getLogger(__name__)


def generate_feedback_reports(
    feedback_ids: List[str],
    batch_id: str,
    source: str = "reports"
) -> Dict[str, Any]:
    """
    Reports queue job: Generate analytics reports and summaries.
    Updates materialized views and pre-computed analytics.

    Args:
        feedback_ids: List of feedback UUIDs to include in reports
        batch_id: Unique identifier for this batch
        source: Source identifier for logging

    Returns:
        Report generation results summary
    """
    logger.info(f"Starting report generation for batch {batch_id} with {len(feedback_ids)} items")

    db = SessionLocal()
    try:
        feedback_repo = FeedbackRepository(db)
        analytics_repo = AnalyticsRepository(db)

        processed = []
        failed = []

        # Generate batch-level analytics
        try:
            # Get sentiment trends for this batch
            batch_sentiment = analytics_repo.get_sentiment_trends(
                date_filter=None,  # Could filter by batch date range
                group_by="day"
            )

            # Get topic distribution
            batch_topics = analytics_repo.get_topic_distribution(
                date_filter=None,
                min_feedback_count=1
            )

            processed.append({
                "report_type": "batch_analytics",
                "sentiment_trends_count": len(batch_sentiment) if batch_sentiment else 0,
                "topic_count": len(batch_topics) if batch_topics else 0
            })

        except Exception as e:
            logger.error(f"Failed to generate batch analytics: {e}")
            failed.append({
                "report_type": "batch_analytics",
                "error": str(e)
            })

        # Generate individual feedback reports
        for feedback_id in feedback_ids:
            try:
                # Get detailed feedback with annotations
                feedback = feedback_repo.get_feedback_by_id(feedback_id)
                if not feedback:
                    failed.append({
                        "id": feedback_id,
                        "error": "Feedback not found"
                    })
                    continue

                # Generate individual report (placeholder)
                report_data = {
                    "feedback_id": feedback_id,
                    "text_length": len(feedback.text),
                    "has_annotation": hasattr(feedback, 'nlp_annotations') and bool(feedback.nlp_annotations),
                    "processing_complete": True
                }

                processed.append(report_data)

            except Exception as e:
                logger.error(f"Failed to generate report for feedback {feedback_id}: {e}")
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

        # Final cache invalidation after reports are complete
        if processed:
            invalidated_keys = cache_service.invalidate_analytics_cache()
            logger.info(f"Invalidated {invalidated_keys} analytics cache keys after report generation")

        logger.info(f"Completed report generation for batch {batch_id}: {len(processed)} reports generated, {len(failed)} failed")
        return result

    except Exception as e:
        logger.error(f"Report generation failed for batch {batch_id}: {e}")
        raise
    finally:
        db.close()


def enqueue_report_generation(
    feedback_ids: List[str],
    batch_id: str,
    source: str = "reports"
) -> str:
    """
    Helper function to enqueue report generation job.

    Returns the job ID for tracking.
    """
    job_id = queue_service.enqueue_job(
        queue_service.QUEUE_REPORTS,
        generate_feedback_reports,
        feedback_ids,
        batch_id,
        source
    )

    if job_id:
        logger.info(f"Enqueued reports job {job_id} for batch {batch_id}")
        return job_id
    else:
        logger.warning("Failed to enqueue reports job, falling back to sync processing")
        # Fallback: process synchronously
        return generate_feedback_reports(feedback_ids, batch_id, source).get("batch_id", "sync-fallback")



