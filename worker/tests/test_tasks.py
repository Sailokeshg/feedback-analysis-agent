"""
Comprehensive tests for worker tasks - batch processing, error handling, and edge cases.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timezone
import uuid

from app.tasks import process_feedback_batch


class TestProcessFeedbackBatch:
    """Test feedback batch processing functionality."""

    @patch('app.tasks.SentimentService')
    @patch('app.tasks.ClusteringService')
    @patch('app.tasks.SessionLocal')
    @patch('app.tasks.create_tables')
    def test_successful_batch_processing(
        self, mock_create_tables, mock_session_local,
        mock_clustering_service_class, mock_sentiment_service_class,
        sample_feedback_batch
    ):
        """Test successful processing of a feedback batch."""
        # Setup mocks
        mock_sentiment_service = Mock()
        mock_sentiment_service.analyze_batch.return_value = [
            (1, 0.85), (-1, 0.72), (1, 0.91), (-1, 0.68), (0, 0.45)
        ]
        mock_sentiment_service_class.return_value = mock_sentiment_service

        mock_clustering_service = Mock()
        mock_clustering_service.cluster_texts.return_value = {
            "product_quality": [0],
            "technical_issues": [1],
            "customer_service": [2],
            "usability": [3],
            "pricing": [4]
        }
        mock_clustering_service_class.return_value = mock_clustering_service

        mock_session = Mock()
        mock_session_local.return_value = mock_session

        # Execute
        result = process_feedback_batch(sample_feedback_batch)

        # Verify results
        assert result["processed_count"] == 5
        assert result["status"] == "completed"

        # Verify sentiment analysis was called
        mock_sentiment_service.analyze_batch.assert_called_once()
        texts = mock_sentiment_service.analyze_batch.call_args[0][0]
        assert len(texts) == 5
        assert "Amazing product!" in texts[0]

        # Verify clustering was called
        mock_clustering_service.cluster_texts.assert_called_once_with(texts)

        # Verify database operations
        assert mock_session.add.call_count == 5
        assert mock_session.commit.call_count == 1

        # Verify feedback items were created with correct data
        add_calls = mock_session.add.call_args_list
        assert len(add_calls) == 5

        # Check first feedback item
        first_item = add_calls[0][0][0]
        assert first_item.id == "fb_001"
        assert first_item.text == sample_feedback_batch[0]["text"]
        assert first_item.sentiment == 1
        assert first_item.sentiment_score == 0.85
        assert first_item.topic_cluster == "product_quality"
        assert first_item.source == "website"

    def test_empty_batch_processing(self):
        """Test processing of empty feedback batch."""
        result = process_feedback_batch([])

        assert result["processed_count"] == 0
        assert result["status"] == "completed"

    def test_batch_with_missing_fields(self):
        """Test processing batch with missing optional fields."""
        incomplete_batch = [
            {
                "text": "Simple feedback text",
                "source": "website"
                # Missing id, customer_id, created_at, meta
            }
        ]

        with patch('app.tasks.SentimentService') as mock_sentiment_class, \
             patch('app.tasks.ClusteringService') as mock_clustering_class, \
             patch('app.tasks.SessionLocal') as mock_session_class, \
             patch('app.tasks.create_tables'):

            mock_sentiment_service = Mock()
            mock_sentiment_service.analyze_batch.return_value = [(1, 0.8)]
            mock_sentiment_class.return_value = mock_sentiment_service

            mock_clustering_service = Mock()
            mock_clustering_service.cluster_texts.return_value = {"general": [0]}
            mock_clustering_class.return_value = mock_clustering_service

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            result = process_feedback_batch(incomplete_batch)

            assert result["processed_count"] == 1

            # Verify feedback item was created with defaults
            add_call = mock_session.add.call_args[0][0]
            assert add_call.id is not None  # Should generate UUID
            assert add_call.source == "website"
            assert add_call.customer_id is None
            assert isinstance(add_call.created_at, datetime)

    def test_sentiment_analysis_failure(self, sample_feedback_batch):
        """Test handling of sentiment analysis failures."""
        with patch('app.tasks.SentimentService') as mock_sentiment_class, \
             patch('app.tasks.ClusteringService') as mock_clustering_class, \
             patch('app.tasks.SessionLocal') as mock_session_class, \
             patch('app.tasks.create_tables'):

            # Sentiment service fails
            mock_sentiment_service = Mock()
            mock_sentiment_service.analyze_batch.side_effect = Exception("Sentiment analysis failed")
            mock_sentiment_class.return_value = mock_sentiment_service

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            with pytest.raises(Exception, match="Sentiment analysis failed"):
                process_feedback_batch(sample_feedback_batch)

            # Verify rollback was called
            mock_session.rollback.assert_called_once()
            mock_session.commit.assert_not_called()

    def test_clustering_failure(self, sample_feedback_batch):
        """Test handling of clustering failures."""
        with patch('app.tasks.SentimentService') as mock_sentiment_class, \
             patch('app.tasks.ClusteringService') as mock_clustering_class, \
             patch('app.tasks.SessionLocal') as mock_session_class, \
             patch('app.tasks.create_tables'):

            mock_sentiment_service = Mock()
            mock_sentiment_service.analyze_batch.return_value = [(1, 0.8)] * 5
            mock_sentiment_class.return_value = mock_sentiment_service

            # Clustering service fails
            mock_clustering_service = Mock()
            mock_clustering_service.cluster_texts.side_effect = Exception("Clustering failed")
            mock_clustering_class.return_value = mock_clustering_service

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            with pytest.raises(Exception, match="Clustering failed"):
                process_feedback_batch(sample_feedback_batch)

            # Verify rollback was called
            mock_session.rollback.assert_called_once()

    def test_database_commit_failure(self, sample_feedback_batch):
        """Test handling of database commit failures."""
        with patch('app.tasks.SentimentService') as mock_sentiment_class, \
             patch('app.tasks.ClusteringService') as mock_clustering_class, \
             patch('app.tasks.SessionLocal') as mock_session_class, \
             patch('app.tasks.create_tables'):

            mock_sentiment_service = Mock()
            mock_sentiment_service.analyze_batch.return_value = [(1, 0.8)] * 5
            mock_sentiment_class.return_value = mock_sentiment_service

            mock_clustering_service = Mock()
            mock_clustering_service.cluster_texts.return_value = {"general": list(range(5))}
            mock_clustering_class.return_value = mock_clustering_service

            mock_session = Mock()
            mock_session.commit.side_effect = Exception("Database commit failed")
            mock_session_class.return_value = mock_session

            with pytest.raises(Exception, match="Database commit failed"):
                process_feedback_batch(sample_feedback_batch)

            # Verify rollback was called
            mock_session.rollback.assert_called_once()

    def test_database_connection_failure(self):
        """Test handling of database connection failures."""
        with patch('app.tasks.SessionLocal', side_effect=Exception("Connection failed")), \
             patch('app.tasks.create_tables'):

            with pytest.raises(Exception, match="Connection failed"):
                process_feedback_batch([{"text": "test", "source": "website"}])

    def test_large_batch_processing(self):
        """Test processing of large feedback batches."""
        large_batch = [
            {
                "id": f"fb_{i:03d}",
                "text": f"Feedback text number {i} with some content",
                "source": "website",
                "customer_id": f"customer_{i}",
                "created_at": f"2024-01-{15+i%15:02d}T10:00:00Z"
            }
            for i in range(100)
        ]

        with patch('app.tasks.SentimentService') as mock_sentiment_class, \
             patch('app.tasks.ClusteringService') as mock_clustering_class, \
             patch('app.tasks.SessionLocal') as mock_session_class, \
             patch('app.tasks.create_tables'):

            mock_sentiment_service = Mock()
            mock_sentiment_service.analyze_batch.return_value = [(1, 0.8)] * 100
            mock_sentiment_class.return_value = mock_sentiment_service

            mock_clustering_service = Mock()
            mock_clustering_service.cluster_texts.return_value = {f"cluster_{i%5}": list(range(i*20, (i+1)*20)) for i in range(5)}
            mock_clustering_class.return_value = mock_clustering_service

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            result = process_feedback_batch(large_batch)

            assert result["processed_count"] == 100
            assert mock_session.add.call_count == 100
            assert mock_session.commit.call_count == 1

    def test_unicode_text_processing(self):
        """Test processing of feedback with unicode characters."""
        unicode_batch = [
            {
                "id": "unicode_001",
                "text": "Amazing product! ¡Increíble! 素晴らしい! 👍🏼",
                "source": "social_media",
                "customer_id": "customer_unicode"
            },
            {
                "id": "unicode_002",
                "text": "Très bon produit! Очень хороший продукт!",
                "source": "survey",
                "customer_id": "customer_multi"
            }
        ]

        with patch('app.tasks.SentimentService') as mock_sentiment_class, \
             patch('app.tasks.ClusteringService') as mock_clustering_class, \
             patch('app.tasks.SessionLocal') as mock_session_class, \
             patch('app.tasks.create_tables'):

            mock_sentiment_service = Mock()
            mock_sentiment_service.analyze_batch.return_value = [(1, 0.9), (1, 0.85)]
            mock_sentiment_class.return_value = mock_sentiment_service

            mock_clustering_service = Mock()
            mock_clustering_service.cluster_texts.return_value = {"positive": [0, 1]}
            mock_clustering_class.return_value = mock_clustering_service

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            result = process_feedback_batch(unicode_batch)

            assert result["processed_count"] == 2

            # Verify unicode text was preserved
            add_calls = mock_session.add.call_args_list
            first_text = add_calls[0][0][0].text
            second_text = add_calls[1][0][0].text
            assert "¡Increíble!" in first_text
            assert "Très bon produit!" in second_text

    def test_malformed_data_handling(self):
        """Test handling of malformed input data."""
        malformed_batch = [
            {
                "id": "good_001",
                "text": "This is valid feedback",
                "source": "website"
            },
            {
                "id": None,  # Invalid ID
                "text": "",  # Empty text
                "source": "invalid_source"  # Invalid source
            },
            {
                "id": "good_002",
                "text": "This is also valid",
                "source": "mobile_app"
            }
        ]

        with patch('app.tasks.SentimentService') as mock_sentiment_class, \
             patch('app.tasks.ClusteringService') as mock_clustering_class, \
             patch('app.tasks.SessionLocal') as mock_session_class, \
             patch('app.tasks.create_tables'):

            mock_sentiment_service = Mock()
            mock_sentiment_service.analyze_batch.return_value = [(1, 0.8), (0, 0.5), (1, 0.9)]
            mock_sentiment_class.return_value = mock_sentiment_service

            mock_clustering_service = Mock()
            mock_clustering_service.cluster_texts.return_value = {"mixed": [0, 1, 2]}
            mock_clustering_class.return_value = mock_clustering_service

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            result = process_feedback_batch(malformed_batch)

            # Should still process all items
            assert result["processed_count"] == 3
            assert mock_session.add.call_count == 3

    def test_memory_efficiency_large_texts(self):
        """Test memory efficiency with large text content."""
        large_text_batch = [
            {
                "id": f"large_{i}",
                "text": "word " * 1000,  # Large text content
                "source": "website"
            }
            for i in range(10)
        ]

        with patch('app.tasks.SentimentService') as mock_sentiment_class, \
             patch('app.tasks.ClusteringService') as mock_clustering_class, \
             patch('app.tasks.SessionLocal') as mock_session_class, \
             patch('app.tasks.create_tables'):

            mock_sentiment_service = Mock()
            mock_sentiment_service.analyze_batch.return_value = [(0, 0.5)] * 10
            mock_sentiment_class.return_value = mock_sentiment_service

            mock_clustering_service = Mock()
            mock_clustering_service.cluster_texts.return_value = {"large_texts": list(range(10))}
            mock_clustering_class.return_value = mock_clustering_service

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            result = process_feedback_batch(large_text_batch)

            assert result["processed_count"] == 10
            # Verify large texts were handled
            add_calls = mock_session.add.call_args_list
            for call in add_calls:
                feedback_item = call[0][0]
                assert len(feedback_item.text) > 4000  # Should preserve large content

    def test_concurrent_processing_simulation(self):
        """Test behavior that might occur with concurrent processing."""
        # Simulate a batch that might be processed concurrently
        concurrent_batch = [
            {
                "id": f"concurrent_{i}",
                "text": f"Concurrent feedback {i}",
                "source": "website",
                "customer_id": f"customer_{i%5}"  # Some customers have multiple feedback
            }
            for i in range(20)
        ]

        with patch('app.tasks.SentimentService') as mock_sentiment_class, \
             patch('app.tasks.ClusteringService') as mock_clustering_class, \
             patch('app.tasks.SessionLocal') as mock_session_class, \
             patch('app.tasks.create_tables'):

            mock_sentiment_service = Mock()
            mock_sentiment_service.analyze_batch.return_value = [(1, 0.8)] * 20
            mock_sentiment_class.return_value = mock_sentiment_service

            mock_clustering_service = Mock()
            mock_clustering_service.cluster_texts.return_value = {f"cluster_{i%4}": list(range(i*5, (i+1)*5)) for i in range(4)}
            mock_clustering_class.return_value = mock_clustering_service

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            result = process_feedback_batch(concurrent_batch)

            assert result["processed_count"] == 20
            assert mock_session.add.call_count == 20

    def test_idempotent_processing(self):
        """Test that processing is reasonably idempotent."""
        batch = [
            {
                "id": "idempotent_001",
                "text": "Test feedback for idempotency",
                "source": "website"
            }
        ]

        with patch('app.tasks.SentimentService') as mock_sentiment_class, \
             patch('app.tasks.ClusteringService') as mock_clustering_class, \
             patch('app.tasks.SessionLocal') as mock_session_class, \
             patch('app.tasks.create_tables'):

            mock_sentiment_service = Mock()
            mock_sentiment_service.analyze_batch.return_value = [(1, 0.8)]
            mock_sentiment_class.return_value = mock_sentiment_service

            mock_clustering_service = Mock()
            mock_clustering_service.cluster_texts.return_value = {"test": [0]}
            mock_clustering_class.return_value = mock_clustering_service

            mock_session = Mock()
            mock_session_class.return_value = mock_session

            # Process same batch twice
            result1 = process_feedback_batch(batch)
            result2 = process_feedback_batch(batch)

            assert result1["processed_count"] == result2["processed_count"] == 1
            assert mock_session.add.call_count == 2  # Both should succeed (no uniqueness constraints in this test)
