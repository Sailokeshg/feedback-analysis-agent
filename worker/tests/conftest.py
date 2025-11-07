"""
Pytest configuration and shared fixtures for worker tests.
"""
import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add server path to sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../server'))


@pytest.fixture
def mock_sentiment_service():
    """Mock sentiment service for worker tests."""
    service = MagicMock()
    service.analyze_batch.return_value = [
        (1, 0.85),   # positive
        (-1, 0.72),  # negative
        (1, 0.91),   # positive
        (-1, 0.68),  # negative
        (0, 0.45)    # neutral
    ]
    return service


@pytest.fixture
def mock_clustering_service():
    """Mock clustering service for worker tests."""
    service = MagicMock()
    service.cluster_texts.return_value = {
        "product_quality": [0],
        "technical_issues": [1],
        "customer_service": [2],
        "usability": [3],
        "pricing": [4]
    }
    return service


@pytest.fixture
def mock_db_session():
    """Mock database session for worker tests."""
    session = MagicMock()
    return session


@pytest.fixture
def sample_feedback_batch():
    """Sample feedback batch for worker processing."""
    return [
        {
            "id": "fb_001",
            "text": "Amazing product! The new dashboard is incredibly intuitive and saves me so much time.",
            "source": "website",
            "customer_id": "customer_001",
            "created_at": "2024-01-15T10:30:00Z",
            "meta": {"user_agent": "Mozilla/5.0", "ip_address": "192.168.1.100"}
        },
        {
            "id": "fb_002",
            "text": "The app keeps crashing when I try to upload photos. Very frustrating experience.",
            "source": "mobile_app",
            "customer_id": "customer_002",
            "created_at": "2024-01-15T11:45:00Z",
            "meta": {"user_agent": "iPhone App v2.1.0", "ip_address": "10.0.0.50"}
        },
        {
            "id": "fb_003",
            "text": "Customer support was incredibly helpful and resolved my issue within minutes.",
            "source": "support_ticket",
            "customer_id": "customer_003",
            "created_at": "2024-01-15T14:20:00Z",
            "meta": {"user_agent": "Zendesk Widget", "ip_address": "203.0.113.1"}
        },
        {
            "id": "fb_004",
            "text": "The interface is confusing and not user-friendly. I had to ask for help multiple times.",
            "source": "survey",
            "customer_id": "customer_004",
            "created_at": "2024-01-15T16:10:00Z",
            "meta": {"user_agent": "SurveyMonkey/1.0", "ip_address": "198.51.100.15"}
        },
        {
            "id": "fb_005",
            "text": "Great value for money! The premium features are worth every penny.",
            "source": "social_media",
            "customer_id": "customer_005",
            "created_at": "2024-01-15T18:30:00Z",
            "meta": {"user_agent": "Twitter/1.0", "ip_address": "104.244.42.1"}
        }
    ]


@pytest.fixture
def mock_feedback_item():
    """Mock feedback item for database operations."""
    item = MagicMock()
    item.id = "test_id"
    return item
