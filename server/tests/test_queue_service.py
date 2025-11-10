"""
Unit tests for queue service functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.queue_service import QueueService


class TestQueueService:
    """Test queue service functionality."""

    def test_queue_service_initialization(self):
        """Test queue service initialization with Redis connection."""
        with patch('app.services.queue_service.Redis') as mock_redis:
            mock_redis.from_url.return_value.ping.return_value = True

            service = QueueService("redis://localhost:6379")

            assert service.redis_conn is not None
            assert len(service.queues) == 4  # ingest, annotate, cluster, reports
            assert QueueService.QUEUE_INGEST in service.queues
            assert QueueService.QUEUE_ANNOTATE in service.queues
            assert QueueService.QUEUE_CLUSTER in service.queues
            assert QueueService.QUEUE_REPORTS in service.queues

    def test_queue_service_no_redis(self):
        """Test queue service initialization without Redis."""
        with patch('app.services.queue_service.Redis') as mock_redis:
            mock_redis.from_url.side_effect = Exception("Connection failed")

            service = QueueService("redis://localhost:6379")

            assert service.redis_conn is None
            assert len(service.queues) == 0

    def test_enqueue_job_success(self):
        """Test successful job enqueuing."""
        with patch('app.services.queue_service.Redis') as mock_redis:
            mock_redis.from_url.return_value.ping.return_value = True

            service = QueueService("redis://localhost:6379")

            # Mock queue
            mock_queue = Mock()
            mock_job = Mock()
            mock_job.id = "test-job-id"
            mock_queue.enqueue.return_value = mock_job
            service.queues[QueueService.QUEUE_INGEST] = mock_queue

            job_id = service.enqueue_job(QueueService.QUEUE_INGEST, test_func, "arg1", "arg2")

            assert job_id == "test-job-id"
            mock_queue.enqueue.assert_called_once_with(
                test_func,
                "arg1",
                "arg2",
                job_timeout=3600,
                result_ttl=86400
            )

    def test_enqueue_job_queue_unavailable(self):
        """Test job enqueuing when queue is unavailable."""
        service = QueueService("redis://localhost:6379")
        # Don't initialize Redis connection

        job_id = service.enqueue_job(QueueService.QUEUE_INGEST, test_func)

        assert job_id is None

    def test_get_queue_stats(self):
        """Test getting queue statistics."""
        with patch('app.services.queue_service.Redis') as mock_redis:
            mock_redis.from_url.return_value.ping.return_value = True

            service = QueueService("redis://localhost:6379")

            # Mock queue with stats
            mock_queue = Mock()
            mock_queue.name = QueueService.QUEUE_INGEST
            mock_queue.started_job_registry.count = 5
            mock_queue.finished_job_registry.count = 10
            mock_queue.failed_job_registry.count = 2
            mock_queue.deferred_job_registry.count = 1

            # Mock len(queue)
            mock_queue.__len__ = Mock(return_value=3)

            service.queues[QueueService.QUEUE_INGEST] = mock_queue

            stats = service.get_queue_stats()

            assert QueueService.QUEUE_INGEST in stats
            queue_stats = stats[QueueService.QUEUE_INGEST]
            assert queue_stats["job_count"] == 3
            assert queue_stats["started_jobs"] == 5
            assert queue_stats["finished_jobs"] == 10
            assert queue_stats["failed_jobs"] == 2
            assert queue_stats["deferred_jobs"] == 1


def test_func():
    """Test function for job enqueuing."""
    return "test"



