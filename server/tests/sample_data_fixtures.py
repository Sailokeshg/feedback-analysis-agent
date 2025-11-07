"""
Sample data fixtures for testing.
"""
import json
import csv
import os
from typing import List, Dict, Any
from datetime import datetime, timezone


def load_sample_feedback_from_jsonl(file_path: str = None) -> List[Dict[str, Any]]:
    """Load sample feedback data from JSONL file."""
    if file_path is None:
        file_path = os.path.join(os.path.dirname(__file__), "test_data", "sample_feedback.jsonl")

    feedback_items = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                item = json.loads(line.strip())
                # Parse the created_at string to datetime
                if isinstance(item.get('created_at'), str):
                    item['created_at'] = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                feedback_items.append(item)

    return feedback_items


def load_sample_feedback_from_csv(file_path: str = None) -> List[Dict[str, Any]]:
    """Load sample feedback data from CSV file."""
    if file_path is None:
        file_path = os.path.join(os.path.dirname(__file__), "test_data", "sample_feedback.csv")

    feedback_items = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert CSV fields to match expected format
            item = {
                'source': row['source'],
                'text': row['text'],
                'customer_id': row['customer_id'],
                'created_at': datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')),
                'meta': {
                    'user_agent': row['user_agent'],
                    'ip_address': row['ip_address']
                }
            }
            feedback_items.append(item)

    return feedback_items


def get_sample_feedback_batch(size: int = 10, format: str = "jsonl") -> List[Dict[str, Any]]:
    """Get a batch of sample feedback data."""
    if format == "csv":
        data = load_sample_feedback_from_csv()
    else:
        data = load_sample_feedback_from_jsonl()

    return data[:size]


def get_diverse_feedback_sample() -> List[Dict[str, Any]]:
    """Get a diverse sample of feedback for comprehensive testing."""
    return [
        {
            "source": "website",
            "text": "This product exceeded my expectations! The quality is outstanding.",
            "customer_id": "positive_001",
            "created_at": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            "meta": {"rating": 5}
        },
        {
            "source": "mobile_app",
            "text": "Terrible experience. App crashes constantly and customer service is unresponsive.",
            "customer_id": "negative_001",
            "created_at": datetime(2024, 1, 15, 11, 45, 0, tzinfo=timezone.utc),
            "meta": {"rating": 1}
        },
        {
            "source": "survey",
            "text": "It's okay, nothing special but it gets the job done.",
            "customer_id": "neutral_001",
            "created_at": datetime(2024, 1, 15, 14, 20, 0, tzinfo=timezone.utc),
            "meta": {"rating": 3}
        },
        {
            "source": "support_ticket",
            "text": "Great support! They helped me immediately and were very knowledgeable.",
            "customer_id": "positive_002",
            "created_at": datetime(2024, 1, 15, 16, 10, 0, tzinfo=timezone.utc),
            "meta": {"resolution_time": "5min"}
        },
        {
            "source": "social_media",
            "text": "Overpriced for what you get. Not worth the money.",
            "customer_id": "negative_002",
            "created_at": datetime(2024, 1, 15, 18, 30, 0, tzinfo=timezone.utc),
            "meta": {"platform": "twitter"}
        }
    ]


def get_feedback_with_topics() -> Dict[str, List[Dict[str, Any]]]:
    """Get sample feedback organized by topics for topic modeling tests."""
    return {
        "product_quality": [
            {
                "source": "website",
                "text": "The build quality is excellent, feels very premium.",
                "customer_id": "pq_001",
                "created_at": datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
            },
            {
                "source": "survey",
                "text": "Product durability is impressive, still works perfectly after years.",
                "customer_id": "pq_002",
                "created_at": datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc)
            }
        ],
        "technical_issues": [
            {
                "source": "mobile_app",
                "text": "App keeps freezing and crashing randomly.",
                "customer_id": "ti_001",
                "created_at": datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
            },
            {
                "source": "support_ticket",
                "text": "Software has multiple bugs that prevent normal usage.",
                "customer_id": "ti_002",
                "created_at": datetime(2024, 1, 15, 13, 0, 0, tzinfo=timezone.utc)
            }
        ],
        "customer_service": [
            {
                "source": "social_media",
                "text": "Customer service was amazing, resolved my issue quickly.",
                "customer_id": "cs_001",
                "created_at": datetime(2024, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
            },
            {
                "source": "survey",
                "text": "Support team is knowledgeable and very helpful.",
                "customer_id": "cs_002",
                "created_at": datetime(2024, 1, 15, 15, 0, 0, tzinfo=timezone.utc)
            }
        ],
        "pricing": [
            {
                "source": "website",
                "text": "Great value for money, competitive pricing.",
                "customer_id": "pr_001",
                "created_at": datetime(2024, 1, 15, 16, 0, 0, tzinfo=timezone.utc)
            },
            {
                "source": "social_media",
                "text": "Too expensive compared to similar products.",
                "customer_id": "pr_002",
                "created_at": datetime(2024, 1, 15, 17, 0, 0, tzinfo=timezone.utc)
            }
        ]
    }
