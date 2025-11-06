"""
Ingest queue jobs for initial data processing and validation.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from ..services.database import SessionLocal
from ..services.cache_service import cache_service
from ..repositories import FeedbackRepository
from ..services.queue_service import queue_service
from ..services.text_processing_service import TextProcessingService

logger = logging.getLogger(__name__)


def process_feedback_ingestion(
    feedback_ids: List[str],
    batch_id: str,
    source: str = "ingest_api"
) -> Dict[str, Any]:
    """
    Ingest queue job: Process newly ingested feedback items.
    Performs text normalization, language detection, and queues for annotation.

    Args:
        feedback_ids: List of feedback UUIDs to process
        batch_id: Unique identifier for this batch
        source: Source identifier for logging

    Returns:
        Processing results summary
    """
    logger.info(f"Starting ingest processing for batch {batch_id} with {len(feedback_ids)} items")

    db = SessionLocal()
    text_processor = TextProcessingService()
    try:
        repo = FeedbackRepository(db)

        processed = []
        failed = []
        skipped_non_english = []

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

                # Perform text processing
                normalized_text, detected_lang, should_process = text_processor.process_text(
                    feedback.text,
                    skip_non_english=True  # Skip non-English for MVP
                )

                # Update feedback with processed data
                feedback.normalized_text = normalized_text
                feedback.detected_language = detected_lang
                db.commit()

                if not should_process:
                    # Skip non-English content
                    skipped_non_english.append({
                        "id": str(feedback.id),
                        "detected_language": detected_lang,
                        "reason": "non_english_content"
                    })
                    continue

                processed.append({
                    "id": str(feedback.id),
                    "text_length": len(feedback.text),
                    "normalized_length": len(normalized_text) if normalized_text else 0,
                    "detected_language": detected_lang,
                    "source": feedback.source
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
            "skipped_non_english_count": len(skipped_non_english),
            "processed": processed,
            "failed": failed,
            "skipped_non_english": skipped_non_english,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Queue successful items for annotation
        if processed:
            annotation_ids = [item["id"] for item in processed]
            queue_service.enqueue_job(
                queue_service.QUEUE_ANNOTATE,
                process_feedback_annotation,
                annotation_ids,
                batch_id,
                source
            )

        logger.info(f"Completed ingest processing for batch {batch_id}: {len(processed)} processed, {len(skipped_non_english)} skipped (non-English), {len(failed)} failed")
        return result

    except Exception as e:
        logger.error(f"Ingest processing failed for batch {batch_id}: {e}")
        raise
    finally:
        db.close()


def enqueue_feedback_ingestion(
    feedback_ids: List[str],
    batch_id: str,
    source: str = "ingest_api"
) -> str:
    """
    Helper function to enqueue ingest processing job.

    Returns the job ID for tracking.
    """
    job_id = queue_service.enqueue_job(
        queue_service.QUEUE_INGEST,
        process_feedback_ingestion,
        feedback_ids,
        batch_id,
        source
    )

    if job_id:
        logger.info(f"Enqueued ingest job {job_id} for batch {batch_id}")
        return job_id
    else:
        logger.warning("Failed to enqueue ingest job, falling back to sync processing")
        # Fallback: process synchronously
        return process_feedback_ingestion(feedback_ids, batch_id, source).get("batch_id", "sync-fallback")
