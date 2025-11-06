"""
Feedback repository for CRUD operations on feedback data.
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from .base import BaseRepository, PaginationParams, DateFilter
from ..models import Feedback, NLPAnnotation

class FeedbackRepository(BaseRepository[Feedback]):
    """Repository for feedback CRUD operations."""

    def __init__(self, session: Session):
        super().__init__(session)

    def create_feedback(
        self,
        source: str,
        text: str,
        customer_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> Feedback:
        """Create a new feedback entry."""
        feedback = Feedback(
            source=source,
            text=text,
            customer_id=customer_id,
            meta=meta or {}
        )

        self.session.add(feedback)
        self.session.commit()
        self.session.refresh(feedback)

        return feedback

    def get_feedback_by_id(self, feedback_id: UUID) -> Optional[Feedback]:
        """Get feedback by ID with annotations."""
        return self.session.query(Feedback).filter(
            Feedback.id == feedback_id
        ).first()

    def get_feedback_list(
        self,
        pagination: Optional[PaginationParams] = None,
        date_filter: Optional[DateFilter] = None,
        source_filter: Optional[str] = None,
        customer_id_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get paginated list of feedback with optional filters."""

        # Base query
        query = """
        SELECT
            f.id, f.source, f.created_at, f.customer_id, f.text,
            f.meta, na.sentiment, na.sentiment_score, na.topic_id
        FROM feedback f
        LEFT JOIN nlp_annotation na ON f.id = na.feedback_id
        """

        params = {}
        conditions = []

        # Apply date filter
        if date_filter:
            date_condition = date_filter.to_sql_condition()
            if date_condition:
                conditions.append(date_condition)
                params.update(date_filter.to_params())

        # Apply source filter
        if source_filter:
            conditions.append("f.source = :source")
            params["source"] = source_filter

        # Apply customer ID filter
        if customer_id_filter:
            conditions.append("f.customer_id = :customer_id")
            params["customer_id"] = customer_id_filter

        # Add WHERE clause if conditions exist
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Apply ordering
        query += " ORDER BY f.created_at DESC"

        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) AS subquery"
        total_count = self.execute_query(count_query, params, fetch="scalar")

        # Apply pagination
        if pagination:
            query, params = self.apply_pagination(query, pagination)

        # Execute query
        results = self.execute_query(query, params, fetch="all")

        return {
            "items": results,
            "total": total_count,
            "page": pagination.page if pagination else 1,
            "page_size": pagination.page_size if pagination else len(results),
            "has_next": (
                pagination.offset + pagination.page_size < total_count
                if pagination else False
            )
        }

    def update_feedback_meta(self, feedback_id: UUID, meta: Dict[str, Any]) -> bool:
        """Update feedback metadata."""
        feedback = self.get_feedback_by_id(feedback_id)
        if not feedback:
            return False

        feedback.meta.update(meta)
        self.session.commit()
        return True

    def delete_feedback(self, feedback_id: UUID) -> bool:
        """Delete feedback and all related annotations."""
        feedback = self.get_feedback_by_id(feedback_id)
        if not feedback:
            return False

        self.session.delete(feedback)
        self.session.commit()
        return True

    def add_nlp_annotation(
        self,
        feedback_id: UUID,
        sentiment: int,
        sentiment_score: float,
        topic_id: Optional[int] = None,
        toxicity_score: Optional[float] = None,
        embedding: Optional[List[float]] = None
    ) -> NLPAnnotation:
        """Add NLP annotation to feedback."""
        feedback = self.get_feedback_by_id(feedback_id)
        if not feedback:
            raise ValueError(f"Feedback with ID {feedback_id} not found")

        annotation = NLPAnnotation(
            feedback_id=feedback_id,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            topic_id=topic_id,
            toxicity_score=toxicity_score,
            embedding=embedding
        )

        self.session.add(annotation)
        self.session.commit()
        self.session.refresh(annotation)

        return annotation

    def get_feedback_with_annotations(
        self,
        feedback_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get feedback with all its annotations."""

        query = """
        SELECT
            f.id, f.source, f.created_at, f.customer_id, f.text, f.meta,
            na.sentiment, na.sentiment_score, na.topic_id, na.toxicity_score,
            t.label as topic_label, t.keywords as topic_keywords
        FROM feedback f
        LEFT JOIN nlp_annotation na ON f.id = na.feedback_id
        LEFT JOIN topic t ON na.topic_id = t.id
        WHERE f.id = :feedback_id
        """

        result = self.execute_query(query, {"feedback_id": feedback_id}, fetch="one")
        return result

    def search_feedback(
        self,
        search_text: Optional[str] = None,
        sentiment_filter: Optional[int] = None,
        topic_id_filter: Optional[int] = None,
        pagination: Optional[PaginationParams] = None,
        date_filter: Optional[DateFilter] = None
    ) -> Dict[str, Any]:
        """Search feedback with multiple filters."""

        query = """
        SELECT
            f.id, f.source, f.created_at, f.customer_id, f.text,
            f.meta, na.sentiment, na.sentiment_score, na.topic_id,
            t.label as topic_label
        FROM feedback f
        LEFT JOIN nlp_annotation na ON f.id = na.feedback_id
        LEFT JOIN topic t ON na.topic_id = t.id
        """

        params = {}
        conditions = []

        # Text search
        if search_text:
            conditions.append("f.text ILIKE :search_text")
            params["search_text"] = f"%{search_text}%"

        # Sentiment filter
        if sentiment_filter is not None:
            conditions.append("na.sentiment = :sentiment")
            params["sentiment"] = sentiment_filter

        # Topic filter
        if topic_id_filter:
            conditions.append("na.topic_id = :topic_id")
            params["topic_id"] = topic_id_filter

        # Date filter
        if date_filter:
            date_condition = date_filter.to_sql_condition()
            if date_condition:
                conditions.append(date_condition)
                params.update(date_filter.to_params())

        # Add WHERE clause if conditions exist
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # Apply ordering
        query += " ORDER BY f.created_at DESC"

        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query}) AS subquery"
        total_count = self.execute_query(count_query, params, fetch="scalar")

        # Apply pagination
        if pagination:
            query, params = self.apply_pagination(query, pagination)

        # Execute query
        results = self.execute_query(query, params, fetch="all")

        return {
            "items": results,
            "total": total_count,
            "page": pagination.page if pagination else 1,
            "page_size": pagination.page_size if pagination else len(results),
            "has_next": (
                pagination.offset + pagination.page_size < total_count
                if pagination else False
            )
        }
