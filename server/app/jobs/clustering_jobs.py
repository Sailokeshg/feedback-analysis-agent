"""
Clustering queue jobs for topic modeling and grouping.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID

from ..services.database import SessionLocal
from ..services.cache_service import cache_service
from ..repositories import FeedbackRepository, TopicRepository
from ..services.queue_service import queue_service
from ..services.clustering_service import ClusteringService

logger = logging.getLogger(__name__)


def process_feedback_clustering(
    feedback_ids: List[str],
    batch_id: str,
    source: str = "clustering"
) -> Dict[str, Any]:
    """
    Clustering queue job: Perform topic modeling and clustering.
    Groups similar feedback items and assigns topic IDs.

    Args:
        feedback_ids: List of feedback UUIDs to cluster
        batch_id: Unique identifier for this batch
        source: Source identifier for logging

    Returns:
        Clustering results summary
    """
    logger.info(f"Starting clustering processing for batch {batch_id} with {len(feedback_ids)} items")

    db = SessionLocal()
    try:
        repo = FeedbackRepository(db)

        clustered = []
        failed = []

        for feedback_id in feedback_ids:
            try:
                # Get feedback item with existing annotation
                feedback = repo.get_feedback_by_id(feedback_id)
                if not feedback:
                    failed.append({
                        "id": feedback_id,
                        "error": "Feedback not found"
                    })
                    continue

                # TODO: Replace with actual clustering algorithm
                # For now, using placeholder topic assignment
                topic_id = None  # Would be determined by clustering algorithm

                # Update annotation with topic if available
                if hasattr(feedback, 'nlp_annotations') and feedback.nlp_annotations:
                    annotation = feedback.nlp_annotations[0]  # Get first annotation
                    # In production, this would update the annotation with topic_id
                    pass

                clustered.append({
                    "id": str(feedback.id),
                    "topic_id": topic_id,
                    "cluster_confidence": 0.0  # Placeholder confidence score
                })

            except Exception as e:
                logger.error(f"Failed to cluster feedback {feedback_id}: {e}")
                failed.append({
                    "id": feedback_id,
                    "error": str(e)
                })

        result = {
            "batch_id": batch_id,
            "source": source,
            "clustered_count": len(clustered),
            "failed_count": len(failed),
            "clustered": clustered,
            "failed": failed,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Queue for reports generation if clustering completed
        if clustered:
            report_ids = [item["id"] for item in clustered]
            queue_service.enqueue_job(
                queue_service.QUEUE_REPORTS,
                generate_feedback_reports,
                report_ids,
                batch_id,
                source
            )

        logger.info(f"Completed clustering processing for batch {batch_id}: {len(clustered)} clustered, {len(failed)} failed")
        return result

    except Exception as e:
        logger.error(f"Clustering processing failed for batch {batch_id}: {e}")
        raise
    finally:
        db.close()


def enqueue_feedback_clustering(
    feedback_ids: List[str],
    batch_id: str,
    source: str = "clustering"
) -> str:
    """
    Helper function to enqueue clustering processing job.

    Returns the job ID for tracking.
    """
    job_id = queue_service.enqueue_job(
        queue_service.QUEUE_CLUSTER,
        process_feedback_clustering,
        feedback_ids,
        batch_id,
        source
    )

    if job_id:
        logger.info(f"Enqueued clustering job {job_id} for batch {batch_id}")
        return job_id
    else:
        logger.warning("Failed to enqueue clustering job, falling back to sync processing")
        # Fallback: process synchronously
        return process_feedback_clustering(feedback_ids, batch_id, source).get("batch_id", "sync-fallback")


def cluster_daily_topics(
    days_back: int = 30,
    min_feedback_count: int = 10,
    batch_id: Optional[str] = None,
    source: str = "daily_clustering"
) -> Dict[str, Any]:
    """
    Daily job to recompute topics from recent feedback.

    Args:
        days_back: Number of days of feedback to include
        min_feedback_count: Minimum feedback items to process
        batch_id: Optional batch ID override
        source: Source identifier

    Returns:
        Clustering results summary
    """
    if batch_id is None:
        batch_id = f"daily_{datetime.utcnow().strftime('%Y%m%d')}"

    logger.info(f"Starting daily topic clustering for batch {batch_id} (last {days_back} days)")

    db = SessionLocal()
    clustering_service = ClusteringService()

    try:
        feedback_repo = FeedbackRepository(db)
        topic_repo = TopicRepository(db)

        # Get feedback from the last N days that has annotations
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Query feedback with annotations from recent period
        recent_feedback = (
            db.query(feedback_repo.model)
            .join(feedback_repo.model.nlp_annotations)
            .filter(feedback_repo.model.created_at >= cutoff_date)
            .filter(feedback_repo.model.normalized_text.isnot(None))  # Only processed feedback
            .all()
        )

        if len(recent_feedback) < min_feedback_count:
            logger.info(f"Only {len(recent_feedback)} feedback items found, skipping clustering")
            return {
                "batch_id": batch_id,
                "source": source,
                "status": "skipped",
                "reason": f"insufficient_data ({len(recent_feedback)} < {min_feedback_count})",
                "feedback_count": len(recent_feedback),
                "timestamp": datetime.utcnow().isoformat()
            }

        logger.info(f"Processing {len(recent_feedback)} feedback items for topic clustering")

        # Extract texts and IDs
        feedback_texts = []
        feedback_items = []

        for feedback in recent_feedback:
            text = feedback.normalized_text or feedback.text
            feedback_texts.append(text)
            feedback_items.append({
                "id": feedback.id,
                "text": text,
                "original_text": feedback.text
            })

        # Perform clustering with keywords
        logger.info("Running clustering algorithm...")
        cluster_info = clustering_service.cluster_texts_with_keywords(
            texts=feedback_texts,
            use_umap=True,  # Use UMAP for better clustering on larger datasets
            max_keywords_per_cluster=15
        )

        # Create/update topics in database
        logger.info(f"Creating/updating {len(cluster_info)} topics...")
        topic_data = []
        feedback_to_topic_updates = []

        for cluster_name, info in cluster_info.items():
            # Skip very small clusters (noise or single items)
            if info["size"] < 3:
                logger.debug(f"Skipping small cluster {cluster_name} with {info['size']} items")
                continue

            topic_data.append({
                "label": info["label"],
                "keywords": info["keywords"]
            })

            # Map feedback items to topic
            for idx in info["indices"]:
                feedback_id = feedback_items[idx]["id"]
                feedback_to_topic_updates.append((feedback_id, None))  # Will be set after topic creation

        # Bulk create/update topics
        topics = topic_repo.bulk_create_topics(topic_data, changed_by="daily_clustering")

        # Update topic mappings
        topic_id_map = {topic.label: topic.id for topic in topics}

        for i, (cluster_name, info) in enumerate(cluster_info.items()):
            if info["size"] < 3:
                continue

            topic_id = topic_id_map.get(info["label"])

            # Update feedback-to-topic mappings
            for idx in info["indices"]:
                feedback_id = feedback_items[idx]["id"]
                feedback_to_topic_updates[idx] = (feedback_id, topic_id)

        # Bulk update annotations with topic IDs
        valid_updates = [(fid, tid) for fid, tid in feedback_to_topic_updates if tid is not None]
        updated_count = feedback_repo.bulk_update_annotation_topics(valid_updates)

        # Refresh materialized views (if any exist)
        # Note: This assumes materialized views exist - adjust as needed
        try:
            db.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY IF EXISTS topic_analytics_view;")
            db.commit()
            logger.info("Refreshed materialized views")
        except Exception as e:
            logger.warning(f"Failed to refresh materialized views: {e}")

        # Invalidate analytics cache
        invalidated_keys = cache_service.invalidate_analytics_cache()
        logger.info(f"Invalidated {invalidated_keys} analytics cache keys")

        result = {
            "batch_id": batch_id,
            "source": source,
            "status": "completed",
            "feedback_processed": len(recent_feedback),
            "topics_created": len(topics),
            "annotations_updated": updated_count,
            "clusters_found": len(cluster_info),
            "days_back": days_back,
            "timestamp": datetime.utcnow().isoformat(),
            "topic_summary": [
                {
                    "id": topic.id,
                    "label": topic.label,
                    "keyword_count": len(topic.keywords or [])
                }
                for topic in topics
            ]
        }

        logger.info(f"Daily topic clustering completed: {len(topics)} topics, {updated_count} annotations updated")
        return result

    except Exception as e:
        logger.error(f"Daily topic clustering failed: {e}")
        raise
    finally:
        db.close()


def enqueue_daily_topic_clustering(
    days_back: int = 30,
    min_feedback_count: int = 10,
    batch_id: Optional[str] = None,
    source: str = "daily_clustering"
) -> str:
    """
    Helper function to enqueue daily topic clustering job.

    Returns the job ID for tracking.
    """
    job_id = queue_service.enqueue_job(
        queue_service.QUEUE_CLUSTER,
        cluster_daily_topics,
        days_back,
        min_feedback_count,
        batch_id,
        source
    )

    if job_id:
        logger.info(f"Enqueued daily topic clustering job {job_id}")
        return job_id
    else:
        logger.warning("Failed to enqueue daily topic clustering job, falling back to sync processing")
        # Fallback: process synchronously
        return cluster_daily_topics(days_back, min_feedback_count, batch_id, source).get("batch_id", "sync-fallback")
