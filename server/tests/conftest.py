"""
Pytest configuration and shared fixtures for server tests.
"""
import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.models.feedback import Base
from app.services.database import SessionLocal


@pytest.fixture(scope="session")
def engine():
    """Create an in-memory SQLite database for testing."""
    # Use SQLite for testing instead of PostgreSQL for simplicity
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a database session for each test function."""
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def mock_feedback_data():
    """Sample feedback data for testing."""
    return [
        {
            "id": str(uuid.uuid4()),
            "source": "website",
            "text": "Great product! I love the new features.",
            "customer_id": "customer_123",
            "created_at": datetime.now(timezone.utc),
            "sentiment": 1,
            "sentiment_score": 0.85,
            "topic_cluster": "product_quality"
        },
        {
            "id": str(uuid.uuid4()),
            "source": "mobile_app",
            "text": "The app crashes frequently. Very disappointed.",
            "customer_id": "customer_456",
            "created_at": datetime.now(timezone.utc),
            "sentiment": -1,
            "sentiment_score": 0.72,
            "topic_cluster": "technical_issues"
        },
        {
            "id": str(uuid.uuid4()),
            "source": "support_ticket",
            "text": "Customer service was helpful and responsive.",
            "customer_id": "customer_789",
            "created_at": datetime.now(timezone.utc),
            "sentiment": 1,
            "sentiment_score": 0.91,
            "topic_cluster": "customer_service"
        },
        {
            "id": str(uuid.uuid4()),
            "source": "survey",
            "text": "Interface is confusing and hard to navigate.",
            "customer_id": "customer_101",
            "created_at": datetime.now(timezone.utc),
            "sentiment": -1,
            "sentiment_score": 0.68,
            "topic_cluster": "usability"
        },
        {
            "id": str(uuid.uuid4()),
            "source": "social_media",
            "text": "Pricing is reasonable for the value provided.",
            "customer_id": "customer_202",
            "created_at": datetime.now(timezone.utc),
            "sentiment": 0,
            "sentiment_score": 0.45,
            "topic_cluster": "pricing"
        }
    ]


@pytest.fixture
def mock_sentiment_service():
    """Mock sentiment service for testing."""
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
    """Mock clustering service for testing."""
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
def mock_embedding_service():
    """Mock embedding service for testing."""
    service = MagicMock()
    # Return mock embeddings (384 dimensions)
    mock_embedding = [0.1] * 384
    service.encode_batch.return_value = [mock_embedding] * 5
    service.encode_single.return_value = mock_embedding
    return service


@pytest.fixture
def sample_feedback_data():
    """Load sample feedback data from test files."""
    from .sample_data_fixtures import get_sample_feedback_batch
    return get_sample_feedback_batch()


@pytest.fixture
def diverse_feedback_sample():
    """Load diverse feedback sample for comprehensive testing."""
    from .sample_data_fixtures import get_diverse_feedback_sample
    return get_diverse_feedback_sample()


@pytest.fixture
def feedback_with_topics():
    """Load feedback organized by topics."""
    from .sample_data_fixtures import get_feedback_with_topics
    return get_feedback_with_topics()
