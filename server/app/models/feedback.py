import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, ARRAY, SmallInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

# Check if pgvector is available, otherwise use bytea for embeddings
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    source = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    customer_id = Column(String, nullable=True)
    text = Column(Text, nullable=False)
    meta = Column(JSONB, nullable=False, default=dict)

    # Relationship to NLP annotations
    nlp_annotations = relationship("NLPAnnotation", back_populates="feedback", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Feedback(id={self.id}, source={self.source})>"


class NLPAnnotation(Base):
    __tablename__ = "nlp_annotation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    feedback_id = Column(UUID(as_uuid=True), ForeignKey("feedback.id", ondelete="CASCADE"), nullable=False, index=True)
    sentiment = Column(SmallInteger, nullable=False)  # -1, 0, 1 for negative, neutral, positive
    sentiment_score = Column(Float, nullable=False)
    topic_id = Column(Integer, ForeignKey("topic.id"), nullable=True, index=True)
    toxicity_score = Column(Float, nullable=True)

    # Embedding field - use pgvector if available, otherwise bytea
    if HAS_PGVECTOR:
        embedding = Column(Vector(384), nullable=True)  # Adjust dimension as needed
    else:
        embedding = Column(sa.LargeBinary, nullable=True)  # bytea fallback

    # Relationships
    feedback = relationship("Feedback", back_populates="nlp_annotations")
    topic = relationship("Topic", back_populates="annotations")

    def __repr__(self):
        return f"<NLPAnnotation(id={self.id}, feedback_id={self.feedback_id}, sentiment={self.sentiment})>"


class Topic(Base):
    __tablename__ = "topic"

    id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String, nullable=False, index=True)
    keywords = Column(ARRAY(String), nullable=False, default=list)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship to NLP annotations
    annotations = relationship("NLPAnnotation", back_populates="topic")

    def __repr__(self):
        return f"<Topic(id={self.id}, label={self.label})>"


class TopicAuditLog(Base):
    __tablename__ = "topic_audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("topic.id"), nullable=False, index=True)
    action = Column(String, nullable=False)  # 'create', 'update', 'delete'
    old_label = Column(String, nullable=True)
    new_label = Column(String, nullable=True)
    old_keywords = Column(ARRAY(String), nullable=True)
    new_keywords = Column(ARRAY(String), nullable=True)
    changed_by = Column(String, nullable=False)  # User identifier
    changed_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    # Relationship to topic
    topic = relationship("Topic")

    def __repr__(self):
        return f"<TopicAuditLog(id={self.id}, topic_id={self.topic_id}, action={self.action})>"
