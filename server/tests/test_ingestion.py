"""
Tests for ingestion functionality - CSV/JSONL parsing, validation, and duplicate detection.
"""

import pytest
import json
import io
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.repositories.feedback import FeedbackRepository
from app.routers.ingest import _parse_csv_data, _parse_jsonl_data

# Test data
VALID_CSV_DATA = """text,created_at,customer_id,rating,category
Great product! Highly recommend,2024-01-15T10:30:00Z,CUST_001,5,electronics
This is okay, nothing special,2024-01-16T14:20:00Z,CUST_002,3,books
Terrible service, very disappointed,2024-01-17T09:15:00Z,CUST_003,1,support
"""

INVALID_CSV_DATA = """text,created_at,customer_id
,CUST_001,5
This has empty text,,CUST_002
Valid text,invalid-date,CUST_003
"""

VALID_JSONL_DATA = """{"text": "Great product! Highly recommend", "created_at": "2024-01-15T10:30:00Z", "customer_id": "CUST_001", "rating": 5, "category": "electronics"}
{"text": "This is okay, nothing special", "created_at": "2024-01-16T14:20:00Z", "customer_id": "CUST_002", "rating": 3, "category": "books"}
{"text": "Terrible service, very disappointed", "created_at": "2024-01-17T09:15:00Z", "customer_id": "CUST_003", "rating": 1, "category": "support"}"""

INVALID_JSONL_DATA = """{"created_at": "2024-01-15T10:30:00Z", "customer_id": "CUST_001"}
{"text": "", "created_at": "2024-01-16T14:20:00Z"}
invalid json line
{"text": "Valid text", "created_at": "invalid-date"}
"""

class TestCSVParser:
    """Test CSV data parsing."""

    def test_parse_valid_csv(self):
        """Test parsing valid CSV data."""
        result = _parse_csv_data(VALID_CSV_DATA)

        assert len(result) == 3

        # Check first item
        item1 = result[0]
        assert item1["text"] == "Great product! Highly recommend"
        assert item1["created_at"] == "2024-01-15T10:30:00Z"
        assert item1["customer_id"] == "CUST_001"
        assert item1["meta"] == {"rating": "5", "category": "electronics"}

        # Check second item
        item2 = result[1]
        assert item2["text"] == "This is okay, nothing special"
        assert item2["created_at"] == "2024-01-16T14:20:00Z"
        assert item2["customer_id"] == "CUST_002"
        assert item2["meta"] == {"rating": "3", "category": "books"}

    def test_parse_invalid_csv(self):
        """Test parsing CSV with invalid/missing data."""
        result = _parse_csv_data(INVALID_CSV_DATA)

        # Should skip empty text rows and invalid dates
        assert len(result) == 1  # Only the valid row should remain
        assert result[0]["text"] == "This has empty text"

    def test_parse_empty_csv(self):
        """Test parsing empty CSV."""
        result = _parse_csv_data("")
        assert result == []

    def test_parse_csv_with_only_headers(self):
        """Test parsing CSV with only headers."""
        result = _parse_csv_data("text,created_at,customer_id")
        assert result == []


class TestJSONLParser:
    """Test JSONL data parsing."""

    def test_parse_valid_jsonl(self):
        """Test parsing valid JSONL data."""
        result = _parse_jsonl_data(VALID_JSONL_DATA)

        assert len(result) == 3

        # Check first item
        item1 = result[0]
        assert item1["text"] == "Great product! Highly recommend"
        assert item1["created_at"] == "2024-01-15T10:30:00Z"
        assert item1["customer_id"] == "CUST_001"
        assert item1["meta"] == {"rating": 5, "category": "electronics"}

    def test_parse_invalid_jsonl(self):
        """Test parsing JSONL with invalid/malformed data."""
        result = _parse_jsonl_data(INVALID_JSONL_DATA)

        # Should skip invalid JSON and empty text
        assert len(result) == 1
        assert result[0]["text"] == "Valid text"

    def test_parse_empty_jsonl(self):
        """Test parsing empty JSONL."""
        result = _parse_jsonl_data("")
        assert result == []

    def test_parse_jsonl_with_empty_lines(self):
        """Test parsing JSONL with empty lines."""
        data = """

{"text": "Valid line"}

"""
        result = _parse_jsonl_data(data)
        assert len(result) == 1
        assert result[0]["text"] == "Valid line"


class TestDuplicateDetection:
    """Test duplicate detection functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.repo = FeedbackRepository(self.mock_session)

    def test_content_hash_generation(self):
        """Test content hash generation for duplicate detection."""
        # Test basic text hash
        hash1 = self.repo._generate_content_hash("Test feedback")
        hash2 = self.repo._generate_content_hash("Test feedback")
        assert hash1 == hash2

        # Test different text produces different hash
        hash3 = self.repo._generate_content_hash("Different feedback")
        assert hash1 != hash3

        # Test with date
        hash4 = self.repo._generate_content_hash("Test feedback", "2024-01-15")
        hash5 = self.repo._generate_content_hash("Test feedback", "2024-01-16")
        assert hash4 != hash5

    def test_duplicate_check_no_existing(self):
        """Test duplicate check when no existing feedback found."""
        # Mock no existing feedback
        self.mock_session.execute.return_value.fetchone.return_value = None

        result = self.repo.check_duplicate("some_hash")
        assert result is None

    def test_duplicate_check_existing(self):
        """Test duplicate check when existing feedback found."""
        from uuid import uuid4
        existing_id = uuid4()

        # Mock existing feedback
        mock_row = Mock()
        mock_row.__getitem__.return_value = str(existing_id)
        self.mock_session.execute.return_value.fetchone.return_value = mock_row

        result = self.repo.check_duplicate("some_hash")
        assert result == existing_id

    @patch('app.repositories.feedback.datetime')
    def test_create_feedback_with_duplicate(self, mock_datetime):
        """Test creating feedback with duplicate detection."""
        mock_datetime.utcnow.return_value = Mock()
        mock_datetime.fromisoformat.return_value = Mock()

        # Mock existing duplicate
        existing_id = "existing-id"
        mock_row = Mock()
        mock_row.__getitem__.return_value = existing_id
        self.mock_session.execute.return_value.fetchone.return_value = mock_row

        # Mock existing feedback
        mock_existing_feedback = Mock()
        mock_existing_feedback.id = existing_id
        mock_existing_feedback.created_at.isoformat.return_value = "2024-01-15T10:00:00"

        with patch.object(self.repo, 'get_feedback_by_id', return_value=mock_existing_feedback):
            feedback, is_duplicate = self.repo.create_feedback_with_duplicate_check(
                source="test",
                text="Duplicate feedback",
                created_at="2024-01-15T10:00:00Z"
            )

            assert is_duplicate is True
            assert feedback == mock_existing_feedback

    @patch('app.repositories.feedback.datetime')
    def test_create_feedback_no_duplicate(self, mock_datetime):
        """Test creating feedback when no duplicate exists."""
        mock_datetime.utcnow.return_value = Mock()

        # Mock no existing duplicate
        self.mock_session.execute.return_value.fetchone.return_value = None

        # Mock new feedback creation
        mock_feedback = Mock()
        mock_feedback.id = "new-id"
        mock_feedback.created_at.isoformat.return_value = "2024-01-15T10:00:00"

        with patch.object(self.repo, 'create_feedback', return_value=mock_feedback):
            feedback, is_duplicate = self.repo.create_feedback_with_duplicate_check(
                source="test",
                text="New feedback",
                created_at="2024-01-15T10:00:00Z"
            )

            assert is_duplicate is False
            assert feedback == mock_feedback


class TestBatchProcessing:
    """Test batch processing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.repo = FeedbackRepository(self.mock_session)

    def test_batch_processing_success(self):
        """Test successful batch processing."""
        feedback_items = [
            {"text": "Great product!", "created_at": "2024-01-15T10:00:00Z"},
            {"text": "Okay product", "created_at": "2024-01-16T10:00:00Z"},
        ]

        # Mock successful processing
        with patch.object(self.repo, 'create_feedback_with_duplicate_check') as mock_create:
            mock_feedback1 = Mock()
            mock_feedback1.id = "id1"
            mock_feedback1.created_at.isoformat.return_value = "2024-01-15T10:00:00"

            mock_feedback2 = Mock()
            mock_feedback2.id = "id2"
            mock_feedback2.created_at.isoformat.return_value = "2024-01-16T10:00:00"

            mock_create.side_effect = [
                (mock_feedback1, False),
                (mock_feedback2, False)
            ]

            result = self.repo.create_feedback_batch(feedback_items, "test_source")

            assert result["summary"]["total_processed"] == 2
            assert result["summary"]["created_count"] == 2
            assert result["summary"]["duplicate_count"] == 0
            assert result["summary"]["error_count"] == 0
            assert len(result["created"]) == 2

    def test_batch_processing_with_duplicates(self):
        """Test batch processing with duplicate detection."""
        feedback_items = [
            {"text": "Duplicate feedback", "created_at": "2024-01-15T10:00:00Z"},
            {"text": "New feedback", "created_at": "2024-01-16T10:00:00Z"},
        ]

        # Mock duplicate detection
        with patch.object(self.repo, 'create_feedback_with_duplicate_check') as mock_create:
            mock_existing_feedback = Mock()
            mock_existing_feedback.id = "existing-id"
            mock_existing_feedback.created_at.isoformat.return_value = "2024-01-15T10:00:00"

            mock_new_feedback = Mock()
            mock_new_feedback.id = "new-id"
            mock_new_feedback.created_at.isoformat.return_value = "2024-01-16T10:00:00"

            mock_create.side_effect = [
                (mock_existing_feedback, True),  # Duplicate
                (mock_new_feedback, False)       # New
            ]

            result = self.repo.create_feedback_batch(feedback_items, "test_source")

            assert result["summary"]["total_processed"] == 2
            assert result["summary"]["created_count"] == 1
            assert result["summary"]["duplicate_count"] == 1
            assert result["summary"]["error_count"] == 0
            assert len(result["created"]) == 1
            assert len(result["duplicates"]) == 1

    def test_batch_processing_with_errors(self):
        """Test batch processing with validation errors."""
        feedback_items = [
            {"text": ""},  # Empty text
            {"text": "Valid text", "created_at": "invalid-date"},
            {"text": "Another valid text"},
        ]

        with patch.object(self.repo, 'create_feedback_with_duplicate_check') as mock_create:
            mock_feedback = Mock()
            mock_feedback.id = "new-id"
            mock_feedback.created_at.isoformat.return_value = "2024-01-15T10:00:00"

            mock_create.side_effect = [
                ValueError("Invalid created_at"),
                (mock_feedback, False)
            ]

            result = self.repo.create_feedback_batch(feedback_items, "test_source")

            assert result["summary"]["total_processed"] == 3
            assert result["summary"]["created_count"] == 1
            assert result["summary"]["error_count"] == 2
            assert len(result["errors"]) == 2


class TestIngestionEndpoint:
    """Test the ingestion endpoint."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    @patch('app.routers.ingest.get_db')
    def test_ingest_csv_success(self, mock_get_db):
        """Test successful CSV ingestion."""
        mock_session = Mock()
        mock_get_db.return_value = mock_session

        # Mock successful batch processing
        with patch('app.routers.ingest.FeedbackRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            mock_repo.create_feedback_batch.return_value = {
                "created": [{"id": "id1", "index": 0}],
                "duplicates": [],
                "errors": [],
                "summary": {
                    "total_processed": 1,
                    "created_count": 1,
                    "duplicate_count": 0,
                    "error_count": 0
                }
            }

            # Mock job enqueue
            with patch('app.routers.ingest.enqueue_feedback_batch_processing', return_value="job-123"):
                csv_content = "text,created_at\nTest feedback,2024-01-15T10:00:00Z"
                files = {"file": ("test.csv", csv_content, "text/csv")}

                response = self.client.post("/ingest/", files=files)

                assert response.status_code == 200
                data = response.json()
                assert data["processed_count"] == 1
                assert data["created_count"] == 1
                assert data["job_id"] == "job-123"

    @patch('app.routers.ingest.get_db')
    def test_ingest_jsonl_success(self, mock_get_db):
        """Test successful JSONL ingestion."""
        mock_session = Mock()
        mock_get_db.return_value = mock_session

        # Mock successful batch processing
        with patch('app.routers.ingest.FeedbackRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            mock_repo.create_feedback_batch.return_value = {
                "created": [{"id": "id1", "index": 0}],
                "duplicates": [],
                "errors": [],
                "summary": {
                    "total_processed": 1,
                    "created_count": 1,
                    "duplicate_count": 0,
                    "error_count": 0
                }
            }

            # Mock job enqueue
            with patch('app.routers.ingest.enqueue_feedback_batch_processing', return_value="job-123"):
                jsonl_content = '{"text": "Test feedback", "created_at": "2024-01-15T10:00:00Z"}'
                files = {"file": ("test.jsonl", jsonl_content, "application/json")}

                response = self.client.post("/ingest/", files=files)

                assert response.status_code == 200
                data = response.json()
                assert data["processed_count"] == 1
                assert data["created_count"] == 1

    def test_ingest_invalid_file_format(self):
        """Test ingestion with invalid file format."""
        files = {"file": ("test.txt", "invalid content", "text/plain")}

        response = self.client.post("/ingest/", files=files)

        assert response.status_code == 400
        assert "File must be CSV" in response.json()["detail"]

    def test_ingest_empty_file(self):
        """Test ingestion with empty file."""
        files = {"file": ("empty.csv", "", "text/csv")}

        response = self.client.post("/ingest/", files=files)

        assert response.status_code == 400
        assert "No valid feedback items found" in response.json()["detail"]

    @patch('app.routers.ingest.get_db')
    def test_ingest_batch_processing_error(self, mock_get_db):
        """Test ingestion when batch processing fails."""
        mock_session = Mock()
        mock_get_db.return_value = mock_session

        # Mock batch processing failure
        with patch('app.routers.ingest.FeedbackRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo_class.return_value = mock_repo

            mock_repo.create_feedback_batch.side_effect = Exception("Database error")

            csv_content = "text\nTest feedback"
            files = {"file": ("test.csv", csv_content, "text/csv")}

            response = self.client.post("/ingest/", files=files)

            assert response.status_code == 500
            assert "Failed to process ingestion" in response.json()["detail"]


class TestIdempotentDuplicateDetection:
    """Test idempotent duplicate detection behavior."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session = Mock(spec=Session)
        self.repo = FeedbackRepository(self.mock_session)

    def test_idempotent_same_text_same_date(self):
        """Test that identical text and date produce same hash."""
        text = "This is a test feedback message"
        date = "2024-01-15T10:30:00Z"

        hash1 = self.repo._generate_content_hash(text, date)
        hash2 = self.repo._generate_content_hash(text, date)

        assert hash1 == hash2

    def test_different_text_different_hash(self):
        """Test that different text produces different hash."""
        text1 = "This is feedback A"
        text2 = "This is feedback B"

        hash1 = self.repo._generate_content_hash(text1)
        hash2 = self.repo._generate_content_hash(text2)

        assert hash1 != hash2

    def test_same_text_different_date_different_hash(self):
        """Test that same text with different dates produce different hashes."""
        text = "Same feedback text"
        date1 = "2024-01-15"
        date2 = "2024-01-16"

        hash1 = self.repo._generate_content_hash(text, date1)
        hash2 = self.repo._generate_content_hash(text, date2)

        assert hash1 != hash2

    def test_case_insensitive_hash(self):
        """Test that hash is case insensitive."""
        text1 = "Test Feedback"
        text2 = "test feedback"

        hash1 = self.repo._generate_content_hash(text1)
        hash2 = self.repo._generate_content_hash(text2)

        assert hash1 == hash2

    def test_whitespace_normalized_hash(self):
        """Test that whitespace is normalized in hash."""
        text1 = "Test   feedback"
        text2 = "Test feedback"

        hash1 = self.repo._generate_content_hash(text1)
        hash2 = self.repo._generate_content_hash(text2)

        assert hash1 == hash2


if __name__ == "__main__":
    pytest.main([__file__])
