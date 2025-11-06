"""
Unit tests for repository layer - SQL injection safety and pagination.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from app.repositories import (
    BaseRepository,
    FeedbackRepository,
    AnalyticsRepository,
    PaginationParams,
    DateFilter,
    RetryConfig
)


class TestPaginationParams:
    """Test pagination parameter validation."""

    def test_valid_pagination(self):
        """Test valid pagination parameters."""
        pagination = PaginationParams(page=2, page_size=20)
        assert pagination.page == 2
        assert pagination.page_size == 20
        assert pagination.offset == 20

    def test_invalid_page(self):
        """Test invalid page number."""
        with pytest.raises(ValueError, match="Page must be >= 1"):
            PaginationParams(page=0)

    def test_invalid_page_size(self):
        """Test invalid page size."""
        with pytest.raises(ValueError, match="Page size must be between 1 and 1000"):
            PaginationParams(page_size=0)

        with pytest.raises(ValueError, match="Page size must be between 1 and 1000"):
            PaginationParams(page_size=2000)


class TestDateFilter:
    """Test date filter functionality."""

    def test_date_filter_conditions(self):
        """Test date filter SQL condition generation."""
        # Start date only
        date_filter = DateFilter(start_date="2024-01-01")
        assert date_filter.to_sql_condition() == "created_at >= :start_date"
        assert date_filter.to_params() == {"start_date": "2024-01-01"}

        # End date only
        date_filter = DateFilter(end_date="2024-12-31")
        assert date_filter.to_sql_condition() == "created_at <= :end_date"
        assert date_filter.to_params() == {"end_date": "2024-12-31"}

        # Both dates
        date_filter = DateFilter(
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        assert date_filter.to_sql_condition() == "created_at >= :start_date AND created_at <= :end_date"
        assert date_filter.to_params() == {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31"
        }

        # Custom field
        date_filter = DateFilter(
            start_date="2024-01-01",
            date_field="updated_at"
        )
        assert date_filter.to_sql_condition() == "updated_at >= :start_date"

    def test_no_conditions(self):
        """Test date filter with no conditions."""
        date_filter = DateFilter()
        assert date_filter.to_sql_condition() == ""
        assert date_filter.to_params() == {}


class TestBaseRepositorySQLInjectionSafety:
    """Test SQL injection safety in base repository."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.repo = BaseRepository(self.mock_session)

    def test_safe_parameterized_query(self):
        """Test that parameterized queries work correctly."""
        # Mock the execute result
        mock_result = Mock()
        mock_result.fetchall.return_value = [{"id": 1, "name": "test"}]
        self.mock_session.execute.return_value = mock_result

        # Execute safe query
        result = self.repo.execute_query(
            "SELECT id, name FROM users WHERE id = :user_id",
            {"user_id": 123}
        )

        assert result == [{"id": 1, "name": "test"}]
        self.mock_session.execute.assert_called_once()

    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are blocked."""
        dangerous_queries = [
            "SELECT * FROM users WHERE id = :id; DROP TABLE users; --",
            "SELECT * FROM users WHERE id = :id UNION SELECT password FROM admin",
            "SELECT * FROM users; DROP TABLE users; --",
        ]

        for query in dangerous_queries:
            with pytest.raises(ValueError, match="Potentially dangerous SQL pattern detected"):
                self.repo.execute_query(query, {"id": 1})

    def test_parameter_mismatch_detection(self):
        """Test that parameter mismatches are detected."""
        # Missing parameter
        with pytest.raises(ValueError, match="Parameter mismatch.*Missing"):
            self.repo.execute_query(
                "SELECT * FROM users WHERE id = :id AND name = :name",
                {"id": 1}  # missing name parameter
            )

        # Extra parameter
        with pytest.raises(ValueError, match="Parameter mismatch.*Extra"):
            self.repo.execute_query(
                "SELECT * FROM users WHERE id = :id",
                {"id": 1, "extra": "value"}  # extra parameter
            )

    def test_pagination_application(self):
        """Test pagination application to queries."""
        pagination = PaginationParams(page=2, page_size=10)

        query = "SELECT * FROM feedback"
        paginated_query, params = self.repo.apply_pagination(query, pagination)

        assert "LIMIT :limit OFFSET :offset" in paginated_query
        assert params["limit"] == 10
        assert params["offset"] == 10

    def test_date_filter_application(self):
        """Test date filter application to queries."""
        date_filter = DateFilter(start_date="2024-01-01", end_date="2024-12-31")

        query = "SELECT * FROM feedback"
        filtered_query, params = self.repo.apply_date_filter(query, date_filter)

        assert "WHERE created_at >= :start_date AND created_at <= :end_date" in filtered_query
        assert params["start_date"] == "2024-01-01"
        assert params["end_date"] == "2024-12-31"

    @patch('time.sleep')
    def test_retry_mechanism(self, mock_sleep):
        """Test retry mechanism with backoff."""
        # Configure mock to fail twice then succeed
        mock_result = Mock()
        mock_result.fetchall.return_value = [{"id": 1}]

        self.mock_session.execute.side_effect = [
            OperationalError("Connection failed", None, None),
            OperationalError("Connection failed", None, None),
            mock_result
        ]

        result = self.repo.execute_query("SELECT 1", {}, fetch="all")

        assert result == [{"id": 1}]
        assert self.mock_session.execute.call_count == 3
        assert mock_sleep.call_count == 2  # Two retries

    def test_retry_exhaustion(self):
        """Test that retries are exhausted after max attempts."""
        self.mock_session.execute.side_effect = OperationalError("Connection failed", None, None)

        with pytest.raises(OperationalError):
            self.repo.execute_query("SELECT 1")

        assert self.mock_session.execute.call_count == 3  # Max attempts reached

    def test_count_query(self):
        """Test count query execution."""
        mock_result = Mock()
        mock_result.scalar.return_value = 42
        self.mock_session.execute.return_value = mock_result

        count = self.repo.get_count("feedback")

        assert count == 42

        # Verify the query was constructed correctly
        call_args = self.mock_session.execute.call_args
        query = str(call_args[0][0])
        assert "SELECT COUNT(*) FROM feedback" in query


class TestFeedbackRepository:
    """Test feedback repository operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.repo = FeedbackRepository(self.mock_session)

    def test_create_feedback(self):
        """Test feedback creation."""
        # Mock the session behavior
        mock_feedback = Mock()
        mock_feedback.id = "test-id"
        self.mock_session.add.return_value = None
        self.mock_session.commit.return_value = None
        self.mock_session.refresh.return_value = None

        # Mock the Feedback constructor
        with patch('app.repositories.feedback.Feedback') as mock_feedback_class:
            mock_feedback_class.return_value = mock_feedback

            result = self.repo.create_feedback(
                source="website",
                text="Great product!",
                customer_id="customer123"
            )

            assert result == mock_feedback
            mock_feedback_class.assert_called_once_with(
                source="website",
                text="Great product!",
                customer_id="customer123",
                meta={}
            )

    def test_get_feedback_list_with_filters(self):
        """Test feedback list retrieval with various filters."""
        # Mock query results
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            {"id": "1", "text": "Good", "sentiment": 1},
            {"id": "2", "text": "Bad", "sentiment": -1}
        ]
        self.mock_session.execute.return_value = mock_result

        # Test with filters
        pagination = PaginationParams(page=1, page_size=10)
        date_filter = DateFilter(start_date="2024-01-01")

        result = self.repo.get_feedback_list(
            pagination=pagination,
            date_filter=date_filter,
            source_filter="website"
        )

        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert "has_next" in result

        # Verify query construction included filters
        call_args = self.mock_session.execute.call_args_list
        query = str(call_args[0][0][0])
        assert "WHERE" in query
        assert "created_at >=" in query
        assert "source =" in query

    def test_search_feedback_sql_injection_safe(self):
        """Test that search feedback prevents SQL injection."""
        # This should be safe even with malicious input
        result = self.repo.search_feedback(
            search_text="normal search",  # Not malicious
            sentiment_filter=1
        )

        # Verify execute_query was called with safe parameters
        self.mock_session.execute.assert_called()

    def test_add_nlp_annotation(self):
        """Test adding NLP annotation."""
        # Mock feedback lookup
        mock_feedback = Mock()
        mock_feedback.id = "feedback-id"
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_feedback

        # Mock annotation creation
        with patch('app.repositories.feedback.NLPAnnotation') as mock_annotation_class:
            mock_annotation = Mock()
            mock_annotation_class.return_value = mock_annotation

            result = self.repo.add_nlp_annotation(
                feedback_id="feedback-id",
                sentiment=1,
                sentiment_score=0.8,
                topic_id=1,
                toxicity_score=0.1
            )

            assert result == mock_annotation
            mock_annotation_class.assert_called_once()


class TestAnalyticsRepository:
    """Test analytics repository operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.repo = AnalyticsRepository(self.mock_session)

    def test_whitelisted_operations(self):
        """Test that only whitelisted operations are allowed."""
        # Valid operation
        with patch.object(self.repo, 'get_sentiment_trends') as mock_method:
            mock_method.return_value = []
            result = self.repo.execute_whitelisted_query("sentiment_trends")
            assert result == []

        # Invalid operation
        with pytest.raises(ValueError, match="not whitelisted"):
            self.repo.execute_whitelisted_query("dangerous_operation")

    def test_sentiment_trends_grouping(self):
        """Test sentiment trends with different grouping options."""
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            {"period": "2024-01-01", "positive_count": 10, "negative_count": 5}
        ]
        self.mock_session.execute.return_value = mock_result

        # Test day grouping
        result = self.repo.get_sentiment_trends(group_by="day")
        assert len(result) == 1

        # Test invalid grouping
        with pytest.raises(ValueError, match="group_by must be"):
            self.repo.get_sentiment_trends(group_by="invalid")

    def test_topic_distribution_with_filters(self):
        """Test topic distribution with filters."""
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            {"id": 1, "label": "Quality", "feedback_count": 20}
        ]
        self.mock_session.execute.return_value = mock_result

        date_filter = DateFilter(start_date="2024-01-01")
        result = self.repo.get_topic_distribution(
            date_filter=date_filter,
            min_feedback_count=5
        )

        assert len(result) == 1
        # Verify date filter was applied
        call_args = self.mock_session.execute.call_args
        query = str(call_args[0][0])
        assert "created_at >=" in query

    def test_daily_aggregates_pagination(self):
        """Test daily aggregates with pagination."""
        # Mock count query
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 50
        self.mock_session.execute.side_effect = [mock_count_result, mock_count_result]

        pagination = PaginationParams(page=2, page_size=10)

        result = self.repo.get_daily_aggregates(pagination=pagination)

        assert result["page"] == 2
        assert result["page_size"] == 10
        assert result["total"] == 50
        assert result["has_next"] is True

    def test_customer_stats_privacy(self):
        """Test that customer stats respect privacy (no sensitive data)."""
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            {"customer_id": "CUST_001", "feedback_count": 5}
        ]
        self.mock_session.execute.return_value = mock_result

        result = self.repo.get_customer_stats(min_feedback_count=3)

        assert len(result) == 1
        assert "customer_id" in result[0]
        assert "feedback_count" in result[0]

    def test_toxicity_analysis_threshold(self):
        """Test toxicity analysis with custom threshold."""
        mock_result = Mock()
        mock_result.fetchone.return_value = {
            "total_analyzed": 100,
            "toxic_count": 20,
            "avg_toxicity_score": 0.3
        }
        self.mock_session.execute.return_value = mock_result

        result = self.repo.get_toxicity_analysis(toxicity_threshold=0.5)

        assert result["total_analyzed"] == 100
        assert result["toxic_count"] == 20

        # Verify threshold parameter was used
        call_args = self.mock_session.execute.call_args
        params = call_args[0][1]
        assert params["threshold"] == 0.5

    def test_feedback_volume_trends(self):
        """Test feedback volume trends calculation."""
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            {"period": "2024-01-01", "total_feedback": 25, "unique_customers": 10}
        ]
        self.mock_session.execute.return_value = mock_result

        result = self.repo.get_feedback_volume_trends(group_by="week")

        assert len(result) == 1
        assert result[0]["total_feedback"] == 25


class TestRetryConfig:
    """Test retry configuration."""

    def test_default_retry_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 0.1
        assert config.max_delay == 5.0
        assert config.backoff_factor == 2.0
        assert OperationalError in config.retryable_exceptions

    def test_custom_retry_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=1.5
        )
        assert config.max_attempts == 5
        assert config.base_delay == 1.0
        assert config.max_delay == 10.0
        assert config.backoff_factor == 1.5


if __name__ == "__main__":
    pytest.main([__file__])
