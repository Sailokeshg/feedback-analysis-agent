"""
Comprehensive API endpoint tests with authentication, error handling, and edge cases.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import json
from datetime import datetime, timezone

from app.main import app
from tests.factories import FeedbackFactory, TopicFactory, NLPAnnotationFactory


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    return Mock()


class TestFeedbackAPI:
    """Test feedback API endpoints."""

    def test_get_feedback_success(self, client, db_session, sample_feedback_data):
        """Test successful feedback retrieval."""
        # Mock the repository
        mock_repo = Mock()
        mock_repo.get_feedback_list.return_value = {
            "items": sample_feedback_data[:2],
            "total": 10,
            "page": 1,
            "page_size": 2,
            "has_next": True
        }

        with patch('app.api.feedback.FeedbackRepository', return_value=mock_repo):
            response = client.get("/api/feedback?page=1&page_size=2")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_next" in data
        assert len(data["items"]) == 2

    def test_get_feedback_with_filters(self, client, db_session):
        """Test feedback retrieval with various filters."""
        mock_repo = Mock()
        mock_repo.get_feedback_list.return_value = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 10,
            "has_next": False
        }

        with patch('app.api.feedback.FeedbackRepository', return_value=mock_repo):
            response = client.get(
                "/api/feedback?page=1&page_size=10&source=website&start_date=2024-01-01&end_date=2024-12-31"
            )

        assert response.status_code == 200
        mock_repo.get_feedback_list.assert_called_once()

    def test_get_feedback_invalid_parameters(self, client):
        """Test feedback retrieval with invalid parameters."""
        # Test invalid page
        response = client.get("/api/feedback?page=0")
        assert response.status_code == 422

        # Test invalid page_size
        response = client.get("/api/feedback?page_size=2000")
        assert response.status_code == 422

    def test_get_feedback_item_success(self, client, db_session):
        """Test successful single feedback item retrieval."""
        mock_feedback = {
            "id": "test-id",
            "text": "Test feedback",
            "source": "website",
            "sentiment": 1,
            "sentiment_score": 0.85
        }

        mock_repo = Mock()
        mock_repo.get_feedback_with_annotations.return_value = mock_feedback

        with patch('app.api.feedback.FeedbackRepository', return_value=mock_repo):
            response = client.get("/api/feedback/test-id")

        assert response.status_code == 200
        assert response.json() == mock_feedback

    def test_get_feedback_item_not_found(self, client, db_session):
        """Test feedback item retrieval when not found."""
        mock_repo = Mock()
        mock_repo.get_feedback_with_annotations.return_value = None

        with patch('app.api.feedback.FeedbackRepository', return_value=mock_repo):
            response = client.get("/api/feedback/nonexistent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_create_feedback_success(self, client, db_session):
        """Test successful feedback creation."""
        feedback_data = {
            "source": "website",
            "text": "Great product!",
            "customer_id": "customer123"
        }

        mock_feedback = Mock()
        mock_feedback.id = "new-id"

        mock_repo = Mock()
        mock_repo.create_feedback.return_value = mock_feedback

        with patch('app.api.feedback.FeedbackRepository', return_value=mock_repo):
            response = client.post("/api/feedback", json=feedback_data)

        assert response.status_code == 201
        assert response.json()["id"] == "new-id"

    def test_create_feedback_validation_error(self, client):
        """Test feedback creation with validation errors."""
        # Missing required fields
        response = client.post("/api/feedback", json={})
        assert response.status_code == 422

        # Invalid source
        response = client.post("/api/feedback", json={
            "source": "invalid_source",
            "text": "Test"
        })
        assert response.status_code == 422

    def test_search_feedback_success(self, client, db_session):
        """Test successful feedback search."""
        mock_repo = Mock()
        mock_repo.search_feedback.return_value = [
            {"id": "1", "text": "Found result", "score": 0.9}
        ]

        with patch('app.api.feedback.FeedbackRepository', return_value=mock_repo):
            response = client.get("/api/feedback/search?q=great+product")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_search_feedback_empty_query(self, client):
        """Test feedback search with empty query."""
        response = client.get("/api/feedback/search?q=")
        assert response.status_code == 400
        assert "query" in response.json()["detail"].lower()


class TestTopicsAPI:
    """Test topics API endpoints."""

    def test_get_topics_success(self, client, db_session):
        """Test successful topics retrieval."""
        mock_topics = [
            {"id": 1, "label": "Quality", "keywords": ["quality", "good", "excellent"]},
            {"id": 2, "label": "Pricing", "keywords": ["price", "cost", "expensive"]}
        ]

        mock_repo = Mock()
        mock_repo.get_all_topics.return_value = mock_topics

        with patch('app.api.topics.TopicRepository', return_value=mock_repo):
            response = client.get("/api/topics")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_topic_success(self, client, db_session):
        """Test successful single topic retrieval."""
        mock_topic = {
            "id": 1,
            "label": "Quality",
            "keywords": ["quality", "good", "excellent"],
            "feedback_count": 25
        }

        mock_repo = Mock()
        mock_repo.get_topic_with_stats.return_value = mock_topic

        with patch('app.api.topics.TopicRepository', return_value=mock_repo):
            response = client.get("/api/topics/1")

        assert response.status_code == 200
        assert response.json()["label"] == "Quality"

    def test_get_topic_not_found(self, client, db_session):
        """Test topic retrieval when not found."""
        mock_repo = Mock()
        mock_repo.get_topic_with_stats.return_value = None

        with patch('app.api.topics.TopicRepository', return_value=mock_repo):
            response = client.get("/api/topics/999")

        assert response.status_code == 404

    def test_create_topic_success(self, client, db_session):
        """Test successful topic creation."""
        topic_data = {
            "label": "New Topic",
            "keywords": ["new", "topic", "keywords"]
        }

        mock_topic = Mock()
        mock_topic.id = 1
        mock_topic.label = "New Topic"

        mock_repo = Mock()
        mock_repo.create_topic.return_value = mock_topic

        with patch('app.api.topics.TopicRepository', return_value=mock_repo):
            response = client.post("/api/topics", json=topic_data)

        assert response.status_code == 201

    def test_update_topic_success(self, client, db_session):
        """Test successful topic update."""
        update_data = {
            "label": "Updated Topic",
            "keywords": ["updated", "keywords"]
        }

        mock_topic = Mock()
        mock_topic.id = 1
        mock_topic.label = "Updated Topic"

        mock_repo = Mock()
        mock_repo.update_topic.return_value = mock_topic

        with patch('app.api.topics.TopicRepository', return_value=mock_repo):
            response = client.put("/api/topics/1", json=update_data)

        assert response.status_code == 200

    def test_delete_topic_success(self, client, db_session):
        """Test successful topic deletion."""
        mock_repo = Mock()
        mock_repo.delete_topic.return_value = True

        with patch('app.api.topics.TopicRepository', return_value=mock_repo):
            response = client.delete("/api/topics/1")

        assert response.status_code == 204


class TestTrendsAPI:
    """Test trends API endpoints."""

    def test_get_sentiment_trends_success(self, client, db_session):
        """Test successful sentiment trends retrieval."""
        mock_trends = [
            {"period": "2024-01-01", "positive_count": 10, "negative_count": 5, "neutral_count": 2},
            {"period": "2024-01-02", "positive_count": 8, "negative_count": 3, "neutral_count": 4}
        ]

        mock_repo = Mock()
        mock_repo.get_sentiment_trends.return_value = mock_trends

        with patch('app.api.trends.AnalyticsRepository', return_value=mock_repo):
            response = client.get("/api/trends/sentiment?group_by=day")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_sentiment_trends_invalid_group_by(self, client):
        """Test sentiment trends with invalid group_by parameter."""
        response = client.get("/api/trends/sentiment?group_by=invalid")
        assert response.status_code == 400

    def test_get_topic_distribution_success(self, client, db_session):
        """Test successful topic distribution retrieval."""
        mock_distribution = [
            {"id": 1, "label": "Quality", "feedback_count": 20, "percentage": 40.0},
            {"id": 2, "label": "Pricing", "feedback_count": 15, "percentage": 30.0}
        ]

        mock_repo = Mock()
        mock_repo.get_topic_distribution.return_value = mock_distribution

        with patch('app.api.trends.AnalyticsRepository', return_value=mock_repo):
            response = client.get("/api/trends/topics")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_customer_stats_success(self, client, db_session):
        """Test successful customer statistics retrieval."""
        mock_stats = [
            {"customer_id": "CUST_001", "feedback_count": 5, "avg_sentiment": 0.7},
            {"customer_id": "CUST_002", "feedback_count": 3, "avg_sentiment": 0.4}
        ]

        mock_repo = Mock()
        mock_repo.get_customer_stats.return_value = mock_stats

        with patch('app.api.trends.AnalyticsRepository', return_value=mock_repo):
            response = client.get("/api/trends/customers")

        assert response.status_code == 200
        assert len(response.json()) == 2


class TestQueryAPI:
    """Test query API endpoints."""

    def test_chat_query_success(self, client):
        """Test successful chat query."""
        query_data = {
            "query": "What are customers saying about our product quality?"
        }

        mock_response = {
            "response": "Based on the feedback analysis...",
            "sources": ["feedback_1", "feedback_2"],
            "confidence": 0.85
        }

        with patch('app.api.query.query_service') as mock_service:
            mock_service.process_query.return_value = mock_response

            response = client.post("/api/query/chat", json=query_data)

        assert response.status_code == 200
        assert "response" in response.json()

    def test_chat_query_empty(self, client):
        """Test chat query with empty input."""
        response = client.post("/api/query/chat", json={"query": ""})
        assert response.status_code == 400

    def test_chat_query_too_long(self, client):
        """Test chat query with overly long input."""
        long_query = "word " * 1000  # Very long query
        response = client.post("/api/query/chat", json={"query": long_query})
        assert response.status_code == 400


class TestUploadAPI:
    """Test upload API endpoints."""

    def test_upload_csv_success(self, client, db_session, sample_feedback_data):
        """Test successful CSV upload."""
        csv_content = """source,text,customer_id,created_at
website,"Great product!","customer1","2024-01-15T10:00:00Z"
mobile_app,"Needs improvement","customer2","2024-01-15T11:00:00Z"
"""

        mock_service = Mock()
        mock_service.process_csv_upload.return_value = {
            "processed_count": 2,
            "errors": []
        }

        with patch('app.api.upload.UploadService', return_value=mock_service):
            response = client.post(
                "/api/upload/csv",
                files={"file": ("test.csv", csv_content, "text/csv")}
            )

        assert response.status_code == 200
        assert response.json()["processed_count"] == 2

    def test_upload_csv_invalid_format(self, client):
        """Test CSV upload with invalid format."""
        invalid_csv = "invalid,csv,content\nwithout,proper,headers"

        response = client.post(
            "/api/upload/csv",
            files={"file": ("test.csv", invalid_csv, "text/csv")}
        )
        assert response.status_code == 400

    def test_upload_jsonl_success(self, client, db_session):
        """Test successful JSONL upload."""
        jsonl_content = """{"source": "website", "text": "Good!", "customer_id": "cust1"}
{"source": "mobile", "text": "Okay", "customer_id": "cust2"}
"""

        mock_service = Mock()
        mock_service.process_jsonl_upload.return_value = {
            "processed_count": 2,
            "errors": []
        }

        with patch('app.api.upload.UploadService', return_value=mock_service):
            response = client.post(
                "/api/upload/jsonl",
                files={"file": ("test.jsonl", jsonl_content, "application/jsonl")}
            )

        assert response.status_code == 200

    def test_upload_jsonl_invalid_json(self, client):
        """Test JSONL upload with invalid JSON."""
        invalid_jsonl = '{"invalid": json content}\n{"also": invalid}'

        response = client.post(
            "/api/upload/jsonl",
            files={"file": ("test.jsonl", invalid_jsonl, "application/jsonl")}
        )
        assert response.status_code == 400


class TestErrorHandling:
    """Test error handling across API endpoints."""

    def test_database_connection_error(self, client):
        """Test handling of database connection errors."""
        with patch('app.api.feedback.get_db', side_effect=Exception("DB connection failed")):
            response = client.get("/api/feedback")

        assert response.status_code == 500

    def test_rate_limiting(self, client):
        """Test rate limiting behavior."""
        # Make multiple requests quickly
        responses = []
        for _ in range(10):
            response = client.get("/api/feedback")
            responses.append(response.status_code)

        # At least some should succeed
        assert 200 in responses

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/feedback")
        assert "access-control-allow-origin" in response.headers

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()
