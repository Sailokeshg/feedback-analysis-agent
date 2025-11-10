"""
Redis RQ queue service for managing multiple job queues.
Provides unified interface for enqueuing jobs across different processing stages.
"""

import logging
from typing import Dict, Any, Optional, List
from redis import Redis
from rq import Queue, Worker

from ..config import settings

logger = logging.getLogger(__name__)


class QueueService:
    """Service for managing Redis RQ queues and job operations."""

    # Queue names
    QUEUE_INGEST = "ingest"
    QUEUE_ANNOTATE = "annotate"
    QUEUE_CLUSTER = "cluster"
    QUEUE_REPORTS = "reports"

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize queue service with Redis connection."""
        self.redis_url = redis_url or settings.external.redis_url
        self.redis_conn = None
        self.queues: Dict[str, Queue] = {}

        if self.redis_url:
            try:
                self.redis_conn = Redis.from_url(self.redis_url)
                # Test connection
                self.redis_conn.ping()
                logger.info("Connected to Redis for job queues")

                # Initialize queues
                self._initialize_queues()
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Queue operations disabled.")
                self.redis_conn = None

    def _initialize_queues(self):
        """Initialize all job queues."""
        if not self.redis_conn:
            return

        queue_names = [self.QUEUE_INGEST, self.QUEUE_ANNOTATE, self.QUEUE_CLUSTER, self.QUEUE_REPORTS]

        for queue_name in queue_names:
            self.queues[queue_name] = Queue(queue_name, connection=self.redis_conn)
            logger.debug(f"Initialized queue: {queue_name}")

    def get_queue(self, queue_name: str) -> Optional[Queue]:
        """Get a queue by name."""
        return self.queues.get(queue_name)

    def enqueue_job(
        self,
        queue_name: str,
        func,
        *args,
        job_timeout: int = 3600,
        result_ttl: int = 86400,
        **kwargs
    ) -> Optional[str]:
        """
        Enqueue a job on the specified queue.

        Args:
            queue_name: Name of the queue
            func: Function to execute
            *args: Positional arguments for the function
            job_timeout: Job timeout in seconds (default: 1 hour)
            result_ttl: Result TTL in seconds (default: 24 hours)
            **kwargs: Keyword arguments for the function

        Returns:
            Job ID if successful, None if queue unavailable
        """
        queue = self.get_queue(queue_name)
        if not queue:
            logger.warning(f"Queue '{queue_name}' not available")
            return None

        try:
            job = queue.enqueue(
                func,
                *args,
                job_timeout=job_timeout,
                result_ttl=result_ttl,
                **kwargs
            )
            logger.info(f"Enqueued job {job.id} on queue '{queue_name}' for function {func.__name__}")
            return job.id
        except Exception as e:
            logger.error(f"Failed to enqueue job on queue '{queue_name}': {e}")
            return None

    def get_job_status(self, queue_name: str, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a job."""
        queue = self.get_queue(queue_name)
        if not queue:
            return None

        try:
            job = queue.fetch_job(job_id)
            if not job:
                return None

            return {
                "job_id": job.id,
                "status": job.get_status(),
                "enqueued_at": job.enqueued_at.isoformat() if job.enqueued_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "ended_at": job.ended_at.isoformat() if job.ended_at else None,
                "result": job.result,
                "exc_info": job.exc_info
            }
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return None

    def get_queue_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all queues."""
        stats = {}

        for queue_name, queue in self.queues.items():
            try:
                stats[queue_name] = {
                    "name": queue_name,
                    "job_count": len(queue),
                    "started_jobs": queue.started_job_registry.count,
                    "finished_jobs": queue.finished_job_registry.count,
                    "failed_jobs": queue.failed_job_registry.count,
                    "deferred_jobs": queue.deferred_job_registry.count
                }
            except Exception as e:
                logger.warning(f"Failed to get stats for queue '{queue_name}': {e}")
                stats[queue_name] = {"name": queue_name, "error": str(e)}

        return stats

    def clear_queue(self, queue_name: str) -> bool:
        """Clear all jobs from a queue."""
        queue = self.get_queue(queue_name)
        if not queue:
            return False

        try:
            queue.empty()
            logger.info(f"Cleared queue '{queue_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to clear queue '{queue_name}': {e}")
            return False


# Global queue service instance
queue_service = QueueService()



