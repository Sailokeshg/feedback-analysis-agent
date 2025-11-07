#!/usr/bin/env python3
"""
Redis RQ worker for processing feedback analysis jobs.
Supports multiple queues: ingest, annotate, cluster, reports.
"""

import os
import sys
import logging
import signal
import time
from typing import List, Optional

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from redis import Redis
from rq import Worker, Queue, Connection
from app.config import settings
from app.services.queue_service import QueueService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiQueueWorker:
    """Worker that can process multiple RQ queues."""

    def __init__(self, queue_names: Optional[List[str]] = None):
        """Initialize worker with specified queues."""
        self.redis_url = settings.external.redis_url or "redis://localhost:6379"
        self.redis_conn = Redis.from_url(self.redis_url)

        # Default to all queues if none specified
        if queue_names is None:
            queue_names = [
                QueueService.QUEUE_INGEST,
                QueueService.QUEUE_ANNOTATE,
                QueueService.QUEUE_CLUSTER,
                QueueService.QUEUE_REPORTS
            ]

        self.queue_names = queue_names
        self.queues = [Queue(name, connection=self.redis_conn) for name in queue_names]
        self.worker = None

        logger.info(f"Initialized MultiQueueWorker for queues: {', '.join(queue_names)}")

    def start(self):
        """Start the worker."""
        try:
            # Test Redis connection
            self.redis_conn.ping()
            logger.info("Connected to Redis successfully")

            # Create worker
            self.worker = Worker(
                self.queues,
                connection=self.redis_conn,
                name=f"feedback-worker-{os.getpid()}"
            )

            logger.info(f"Starting worker {self.worker.name} for queues: {self.queue_names}")

            # Start processing
            self.worker.work()

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down worker")
            self.stop()
        except Exception as e:
            logger.error(f"Worker failed to start: {e}")
            sys.exit(1)

    def stop(self):
        """Stop the worker gracefully."""
        if self.worker:
            logger.info("Stopping worker gracefully")
            self.worker.stop()

    def get_queue_stats(self):
        """Get statistics for all monitored queues."""
        stats = {}
        for queue in self.queues:
            try:
                stats[queue.name] = {
                    "name": queue.name,
                    "job_count": len(queue),
                    "started_jobs": queue.started_job_registry.count,
                    "finished_jobs": queue.finished_job_registry.count,
                    "failed_jobs": queue.failed_job_registry.count,
                    "deferred_jobs": queue.deferred_job_registry.count
                }
            except Exception as e:
                logger.warning(f"Failed to get stats for queue '{queue.name}': {e}")
                stats[queue.name] = {"name": queue.name, "error": str(e)}

        return stats


def main():
    """Main entry point for the worker."""
    import argparse

    parser = argparse.ArgumentParser(description="Feedback Analysis RQ Worker")
    parser.add_argument(
        "--queues",
        nargs="+",
        choices=[QueueService.QUEUE_INGEST, QueueService.QUEUE_ANNOTATE,
                QueueService.QUEUE_CLUSTER, QueueService.QUEUE_REPORTS],
        help="Queues to process (default: all queues)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print queue statistics and exit"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create worker
    worker = MultiQueueWorker(args.queues)

    if args.stats:
        # Print queue statistics
        stats = worker.get_queue_stats()
        print("\nQueue Statistics:")
        print("=" * 50)
        for queue_name, queue_stats in stats.items():
            if "error" in queue_stats:
                print(f"{queue_name}: ERROR - {queue_stats['error']}")
            else:
                print(f"{queue_name}:")
                print(f"  Pending jobs: {queue_stats['job_count']}")
                print(f"  Started jobs: {queue_stats['started_jobs']}")
                print(f"  Finished jobs: {queue_stats['finished_jobs']}")
                print(f"  Failed jobs: {queue_stats['failed_jobs']}")
                print(f"  Deferred jobs: {queue_stats['deferred_jobs']}")
        return

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown")
        worker.stop()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Start the worker
    worker.start()


if __name__ == "__main__":
    main()

