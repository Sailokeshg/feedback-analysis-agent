"""
Annotation queue jobs for NLP processing and sentiment analysis.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from ..services.database import SessionLocal
from ..services.cache_service import cache_service
from ..repositories import FeedbackRepository
from ..services.queue_service import queue_service
from ..services.embedding_service import EmbeddingService
from ..services.sentiment_service import SentimentService
from .clustering_jobs import process_feedback_clustering

logger = logging.getLogger(__name__)


def process_feedback_annotation(
    feedback_ids: List[str],
    batch_id: str,
    source: str = "annotation"
) -> Dict[str, Any]:
    """
    Annotation queue job: Perform NLP analysis on feedback items.
    Includes sentiment analysis, toxicity detection, and topic classification.

    Args:
        feedback_ids: List of feedback UUIDs to annotate
        batch_id: Unique identifier for this batch
        source: Source identifier for logging

    Returns:
        Annotation results summary
    """
    logger.info(f"Starting annotation processing for batch {batch_id} with {len(feedback_ids)} items")

    db = SessionLocal()
    embedding_service = EmbeddingService()
    sentiment_service = SentimentService()
    try:
        repo = FeedbackRepository(db)

        annotated = []
        failed = []

        # Collect texts for batch embedding generation
        feedback_texts = []
        feedback_items = []

        # First pass: collect all feedback items and texts
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

                # Use normalized text for processing if available, otherwise fall back to original
                text_to_process = feedback.normalized_text or feedback.text

                feedback_texts.append(text_to_process)
                feedback_items.append((feedback, text_to_process))

            except Exception as e:
                logger.error(f"Failed to load feedback {feedback_id}: {e}")
                failed.append({
                    "id": feedback_id,
                    "error": str(e)
                })

        # Generate embeddings in batch
        embeddings = None
        if feedback_texts and embedding_service.model:
            logger.info(f"Generating embeddings for {len(feedback_texts)} texts")
            embeddings = embedding_service.generate_embeddings(feedback_texts)

            if embeddings is not None:
                logger.info(f"Successfully generated {len(embeddings)} embeddings")

                # Store embeddings in ChromaDB
                chroma_ids = [f"feedback_{item[0].id}" for item in feedback_items]
                embedding_service.store_embeddings_chroma(
                    embeddings=embeddings,
                    texts=[item[1] for item in feedback_items],
                    ids=chroma_ids,
                    metadata=[{"feedback_id": str(item[0].id), "source": item[0].source} for item in feedback_items]
                )
            else:
                logger.warning("Failed to generate embeddings, proceeding without them")
        else:
            logger.warning("Embedding service not available or no texts to embed")

        # Second pass: create annotations with embeddings and sentiment
        for i, (feedback, text_to_process) in enumerate(feedback_items):
            try:
                # Analyze sentiment using the configured strategy
                sentiment, sentiment_score = sentiment_service.analyze_sentiment(text_to_process)

                # Get embedding for this feedback item
                embedding = embeddings[i].tolist() if embeddings is not None else None

                # Placeholder toxicity score (could be enhanced later)
                toxicity_score = 0.1  # Low toxicity placeholder
                topic_id = None  # Will be determined by clustering

                # Log that we're using normalized text when available
                if feedback.normalized_text:
                    logger.debug(f"Using normalized text for feedback {feedback.id} (length: {len(text_to_process)})")

                # Log sentiment analysis result
                sentiment_label = sentiment_service.get_sentiment_label(sentiment)
                logger.debug(f"Sentiment analysis for feedback {feedback.id}: {sentiment_label} ({sentiment_score:.3f})")

                # Add NLP annotation with embedding and sentiment
                annotation = repo.add_nlp_annotation(
                    feedback_id=feedback.id,
                    sentiment=sentiment,
                    sentiment_score=sentiment_score,
                    topic_id=topic_id,
                    toxicity_score=toxicity_score,
                    embedding=embedding
                )

                annotated.append({
                    "id": str(feedback.id),
                    "sentiment": sentiment,
                    "sentiment_score": sentiment_score,
                    "sentiment_label": sentiment_label,
                    "toxicity_score": toxicity_score,
                    "annotation_id": annotation.id if annotation else None,
                    "embedding_generated": embedding is not None
                })

            except Exception as e:
                logger.error(f"Failed to annotate feedback {feedback.id}: {e}")
                failed.append({
                    "id": str(feedback.id),
                    "error": str(e)
                })

        result = {
            "batch_id": batch_id,
            "source": source,
            "annotated_count": len(annotated),
            "failed_count": len(failed),
            "annotated": annotated,
            "failed": failed,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Queue successful annotations for clustering
        if annotated:
            cluster_ids = [item["id"] for item in annotated]
            queue_service.enqueue_job(
                queue_service.QUEUE_CLUSTER,
                process_feedback_clustering,
                cluster_ids,
                batch_id,
                source
            )

        # Invalidate analytics cache after annotation
        if annotated:
            invalidated_keys = cache_service.invalidate_analytics_cache()
            logger.info(f"Invalidated {invalidated_keys} analytics cache keys after annotation")

        logger.info(f"Completed annotation processing for batch {batch_id}: {len(annotated)} annotated, {len(failed)} failed")
        return result

    except Exception as e:
        logger.error(f"Annotation processing failed for batch {batch_id}: {e}")
        raise
    finally:
        db.close()


def enqueue_feedback_annotation(
    feedback_ids: List[str],
    batch_id: str,
    source: str = "annotation"
) -> str:
    """
    Helper function to enqueue annotation processing job.

    Returns the job ID for tracking.
    """
    job_id = queue_service.enqueue_job(
        queue_service.QUEUE_ANNOTATE,
        process_feedback_annotation,
        feedback_ids,
        batch_id,
        source
    )

    if job_id:
        logger.info(f"Enqueued annotation job {job_id} for batch {batch_id}")
        return job_id
    else:
        logger.warning("Failed to enqueue annotation job, falling back to sync processing")
        # Fallback: process synchronously
        return process_feedback_annotation(feedback_ids, batch_id, source).get("batch_id", "sync-fallback")
