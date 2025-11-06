from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class FeedbackItem(Base):
    __tablename__ = "feedback_items"

    id = Column(String, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    sentiment = Column(String, nullable=False)  # positive, negative, neutral
    sentiment_score = Column(Float, nullable=False)
    topic_cluster = Column(String, nullable=False)
    source = Column(String, nullable=False)  # CSV upload, API, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<FeedbackItem(id={self.id}, sentiment={self.sentiment})>"
