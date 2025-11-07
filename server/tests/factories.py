"""
Factory Boy factories for creating test data.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import factory
from factory.alchemy import SQLAlchemyModelFactory

from app.models.feedback import Feedback, NLPAnnotation, Topic, TopicAuditLog


class FeedbackFactory(SQLAlchemyModelFactory):
    """Factory for creating Feedback instances."""

    class Meta:
        model = Feedback
        sqlalchemy_session_persistence = "commit"

    id = factory.LazyFunction(uuid.uuid4)
    source = factory.Faker("random_element", elements=["website", "mobile_app", "support_ticket", "survey", "social_media"])
    created_at = factory.Faker("date_time_this_year", tzinfo=timezone.utc)
    customer_id = factory.Faker("uuid4")
    text = factory.Faker("sentence", nb_words=12)
    normalized_text = factory.LazyAttribute(lambda obj: obj.text.lower() if obj.text else None)
    detected_language = factory.Faker("language_code")
    meta = factory.Dict({
        "user_agent": factory.Faker("user_agent"),
        "ip_address": factory.Faker("ipv4"),
        "session_id": factory.Faker("uuid4")
    })


class TopicFactory(SQLAlchemyModelFactory):
    """Factory for creating Topic instances."""

    class Meta:
        model = Topic
        sqlalchemy_session_persistence = "commit"

    label = factory.Faker("word")
    keywords = factory.List([
        factory.Faker("word"),
        factory.Faker("word"),
        factory.Faker("word"),
        factory.Faker("word")
    ])
    updated_at = factory.Faker("date_time_this_year", tzinfo=timezone.utc)


class NLPAnnotationFactory(SQLAlchemyModelFactory):
    """Factory for creating NLPAnnotation instances."""

    class Meta:
        model = NLPAnnotation
        sqlalchemy_session_persistence = "commit"

    feedback = factory.SubFactory(FeedbackFactory)
    sentiment = factory.Faker("random_element", elements=[-1, 0, 1])
    sentiment_score = factory.Faker("pyfloat", min_value=0.0, max_value=1.0)
    topic = factory.SubFactory(TopicFactory)
    toxicity_score = factory.Faker("pyfloat", min_value=0.0, max_value=1.0)
    # Note: embedding field is handled separately as it depends on pgvector availability


class TopicAuditLogFactory(SQLAlchemyModelFactory):
    """Factory for creating TopicAuditLog instances."""

    class Meta:
        model = TopicAuditLog
        sqlalchemy_session_persistence = "commit"

    topic = factory.SubFactory(TopicFactory)
    action = factory.Faker("random_element", elements=["create", "update", "delete"])
    old_label = factory.Faker("word")
    new_label = factory.Faker("word")
    old_keywords = factory.List([
        factory.Faker("word"),
        factory.Faker("word")
    ])
    new_keywords = factory.List([
        factory.Faker("word"),
        factory.Faker("word"),
        factory.Faker("word")
    ])
    changed_by = factory.Faker("email")
    changed_at = factory.Faker("date_time_this_year", tzinfo=timezone.utc)
    ip_address = factory.Faker("ipv4")
    user_agent = factory.Faker("user_agent")


# Convenience functions for creating test data
def create_feedback_batch(count: int = 5) -> List[Feedback]:
    """Create a batch of feedback items for testing."""
    return FeedbackFactory.create_batch(count)


def create_topics_with_feedback(
    topic_count: int = 3,
    feedback_per_topic: int = 5
) -> tuple[List[Topic], List[Feedback]]:
    """Create topics and associated feedback for testing."""
    topics = TopicFactory.create_batch(topic_count)

    all_feedback = []
    for topic in topics:
        # Create feedback and annotations linked to this topic
        feedback_items = FeedbackFactory.create_batch(feedback_per_topic)
        for feedback in feedback_items:
            NLPAnnotationFactory.create(
                feedback=feedback,
                topic=topic,
                sentiment=factory.Faker("random_element", elements=[-1, 0, 1]),
                sentiment_score=factory.Faker("pyfloat", min_value=0.0, max_value=1.0)
            )
        all_feedback.extend(feedback_items)

    return topics, all_feedback
