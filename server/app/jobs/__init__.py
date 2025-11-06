"""
RQ jobs for background processing across multiple queues.
"""

# Legacy batch processing (keeping for backward compatibility)
from .batch_processing import process_feedback_batch, enqueue_feedback_batch_processing

# Multi-queue job processing
from .ingest_jobs import process_feedback_ingestion, enqueue_feedback_ingestion
from .annotation_jobs import process_feedback_annotation, enqueue_feedback_annotation
from .clustering_jobs import (
    process_feedback_clustering,
    enqueue_feedback_clustering,
    cluster_daily_topics,
    enqueue_daily_topic_clustering
)
from .reports_jobs import generate_feedback_reports, enqueue_report_generation

__all__ = [
    # Legacy functions
    "process_feedback_batch",
    "enqueue_feedback_batch_processing",

    # Multi-queue processing
    "process_feedback_ingestion",
    "enqueue_feedback_ingestion",
    "process_feedback_annotation",
    "enqueue_feedback_annotation",
    "process_feedback_clustering",
    "enqueue_feedback_clustering",
    "cluster_daily_topics",
    "enqueue_daily_topic_clustering",
    "generate_feedback_reports",
    "enqueue_report_generation"
]
