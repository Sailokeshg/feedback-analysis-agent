#!/usr/bin/env python3
"""
Seed script for populating the database with fake feedback data.
Run with: python scripts/seed_database.py
"""

import sys
import os
from datetime import datetime, timedelta
import random
import uuid
from faker import Faker

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.database import SessionLocal, get_db
from app.models import Feedback, NLPAnnotation, Topic

fake = Faker()

# Sample topics and their keywords
TOPICS_DATA = [
    {
        "label": "Product Quality",
        "keywords": ["quality", "durability", "build", "materials", "craftsmanship"]
    },
    {
        "label": "Customer Service",
        "keywords": ["support", "service", "help", "response", "agent"]
    },
    {
        "label": "Pricing",
        "keywords": ["price", "cost", "expensive", "cheap", "value"]
    },
    {
        "label": "Shipping & Delivery",
        "keywords": ["shipping", "delivery", "fast", "slow", "tracking"]
    },
    {
        "label": "User Experience",
        "keywords": ["interface", "design", "usability", "easy", "difficult"]
    }
]

# Sample feedback sources
SOURCES = ["website", "mobile_app", "email", "social_media", "survey", "support_ticket"]

# Sample customer IDs
CUSTOMER_IDS = [f"CUST_{i:04d}" for i in range(1, 101)] + [None] * 50  # 50% anonymous

def create_topics(db):
    """Create sample topics"""
    topics = []
    for topic_data in TOPICS_DATA:
        topic = Topic(
            label=topic_data["label"],
            keywords=topic_data["keywords"]
        )
        db.add(topic)
        topics.append(topic)

    db.commit()
    print(f"Created {len(topics)} topics")
    return topics

def generate_fake_feedback():
    """Generate fake feedback data"""
    # Generate random dates within the last 30 days
    days_ago = random.randint(0, 30)
    created_at = datetime.utcnow() - timedelta(days=days_ago)

    # Random source
    source = random.choice(SOURCES)

    # Random customer (50% chance of being anonymous)
    customer_id = random.choice(CUSTOMER_IDS)

    # Generate fake feedback text based on sentiment
    sentiment_options = [-1, 0, 1]  # negative, neutral, positive
    sentiment_weights = [0.2, 0.3, 0.5]  # 20% negative, 30% neutral, 50% positive
    sentiment = random.choices(sentiment_options, weights=sentiment_weights)[0]

    if sentiment == 1:
        templates = [
            "I absolutely love this product! The {feature} is amazing.",
            "Great experience overall. The {feature} exceeded my expectations.",
            "Highly recommend! The {feature} makes all the difference.",
            "Fantastic service and quality. Really impressed with the {feature}."
        ]
    elif sentiment == 0:
        templates = [
            "It's okay. The {feature} is neither good nor bad.",
            "Average experience. The {feature} works as expected.",
            "Decent product. Nothing special about the {feature}.",
            "It's fine. The {feature} meets basic requirements."
        ]
    else:  # negative
        templates = [
            "Very disappointed with the {feature}. It doesn't work well.",
            "Poor quality. The {feature} is frustrating to use.",
            "Not satisfied. The {feature} has many issues.",
            "Terrible experience. The {feature} is completely broken."
        ]

    features = ["design", "performance", "reliability", "support", "pricing", "delivery"]
    text = random.choice(templates).format(feature=random.choice(features))

    # Generate metadata
    meta = {
        "rating": random.randint(1, 5) if random.random() > 0.3 else None,
        "channel": source,
        "verified": random.choice([True, False]),
        "tags": random.sample(["urgent", "complaint", "praise", "suggestion", "bug"], random.randint(0, 2))
    }

    return {
        "id": uuid.uuid4(),
        "source": source,
        "created_at": created_at,
        "customer_id": customer_id,
        "text": text,
        "meta": meta,
        "sentiment": sentiment
    }

def create_feedback_and_annotations(db, topics, num_feedback=100):
    """Create feedback entries with NLP annotations"""
    feedback_items = []

    for _ in range(num_feedback):
        feedback_data = generate_fake_feedback()

        # Create feedback entry
        feedback = Feedback(
            id=feedback_data["id"],
            source=feedback_data["source"],
            created_at=feedback_data["created_at"],
            customer_id=feedback_data["customer_id"],
            text=feedback_data["text"],
            meta=feedback_data["meta"]
        )

        db.add(feedback)

        # Create NLP annotation
        sentiment = feedback_data["sentiment"]
        sentiment_score = random.uniform(0.1, 0.9) if sentiment == 0 else (
            random.uniform(0.6, 0.95) if sentiment == 1 else random.uniform(0.05, 0.4)
        )

        # Assign topic (70% chance)
        topic = random.choice(topics) if random.random() > 0.3 else None

        # Generate fake embedding (simplified as list of floats)
        embedding = [random.uniform(-1, 1) for _ in range(384)] if random.random() > 0.2 else None

        annotation = NLPAnnotation(
            feedback_id=feedback.id,
            sentiment=sentiment,
            sentiment_score=round(sentiment_score, 4),
            topic_id=topic.id if topic else None,
            toxicity_score=round(random.uniform(0, 0.8), 4) if random.random() > 0.6 else None,
            embedding=embedding
        )

        db.add(annotation)
        feedback_items.append(feedback)

    db.commit()
    print(f"Created {len(feedback_items)} feedback entries with annotations")
    return feedback_items

def main():
    """Main seeding function"""
    print("Starting database seeding...")

    db = SessionLocal()
    try:
        # Create topics
        topics = create_topics(db)

        # Create feedback and annotations
        create_feedback_and_annotations(db, topics, num_feedback=200)

        print("Database seeding completed successfully!")
        print("\nSummary:")
        print("- 5 topics created")
        print("- 200 feedback entries created")
        print("- NLP annotations generated for all feedback")
        print("- Materialized view will be automatically updated")

    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
