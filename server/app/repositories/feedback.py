"""
Feedback repository for CRUD operations on feedback data.
"""

import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text

from .base import BaseRepository, PaginationParams, DateFilter
from ..models import Feedback, NLPAnnotation

class FeedbackRepository(BaseRepository[Feedback]):
    """Repository for feedback CRUD operations."""

    def __init__(self, session: Session):
        super().__init__(session)

    def _generate_content_hash(self, text: str, created_at: Optional[str] = None) -> str:
        """Generate a hash for duplicate detection based on text and creation date."""
        content = text.strip().lower()
        if created_at:
            # Normalize the date to YYYY-MM-DD format for consistent hashing
            try:
                if isinstance(created_at, str):
                    # Parse various date formats and normalize
                    parsed_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    date_str = parsed_date.date().isoformat()
                else:
                    date_str = created_at.date().isoformat()
                content += f"|{date_str}"
            except (ValueError, AttributeError):
                # If date parsing fails, just use the text
                pass

        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def check_duplicate(self, content_hash: str) -> Optional[UUID]:
        """Check if feedback with this content hash already exists."""
        query = "SELECT id FROM feedback WHERE meta->>'content_hash' = :content_hash LIMIT 1"
        result = self.execute_query(query, {"content_hash": content_hash}, fetch="one")
        return UUID(result["id"]) if result else None

    def create_feedback(
        self,
        source: str,
        text: str,
        customer_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None
    ) -> Feedback:
        """Create a new feedback entry."""
        feedback = Feedback(
            source=source,
            text=text,
            customer_id=customer_id,
            meta=meta or {},
            created_at=created_at or datetime.utcnow()
        )

        self.session.add(feedback)
        self.session.commit()
        self.session.refresh(feedback)

        return feedback

    def create_feedback_with_duplicate_check(
        self,
        source: str,
        text: str,
        customer_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None
    ) -> Tuple[Feedback, bool]:
        """
        Create feedback with duplicate detection.
        Returns (feedback, is_duplicate)
        """
        # Generate content hash for duplicate detection
        content_hash = self._generate_content_hash(text, created_at.isoformat() if created_at else None)

        # Check for existing feedback with same hash
        existing_id = self.check_duplicate(content_hash)
        if existing_id:
            # Return existing feedback and mark as duplicate
            existing_feedback = self.get_feedback_by_id(existing_id)
            return existing_feedback, True

        # Create new feedback with hash in meta
        if meta is None:
            meta = {}
        meta["content_hash"] = content_hash

        feedback = self.create_feedback(
            source=source,
            text=text,
            customer_id=customer_id,
            meta=meta,
            created_at=created_at
        )

        return feedback, False

    def create_feedback_batch(
        self,
        feedback_items: List[Dict[str, Any]],
        source: str = "batch_ingest"
    ) -> Dict[str, Any]:
        """
        Create multiple feedback items with duplicate detection.
        Returns summary of created and duplicate items.
        """
        created = []
        duplicates = []
        errors = []

        for i, item in enumerate(feedback_items):
            try:
                # Validate required fields
                if "text" not in item or not item["text"].strip():
                    errors.append({
                        "index": i,
                        "error": "Missing or empty 'text' field"
                    })
                    continue

                # Parse optional fields
                customer_id = item.get("customer_id")
                meta = item.get("meta", {})

                # Parse created_at if provided
                created_at = None
                if "created_at" in item and item["created_at"]:
                    try:
                        created_at = datetime.fromisoformat(item["created_at"].replace('Z', '+00:00'))
                    except ValueError:
                        errors.append({
                            "index": i,
                            "error": f"Invalid created_at format: {item['created_at']}"
                        })
                        continue

                # Create feedback with duplicate check
                feedback, is_duplicate = self.create_feedback_with_duplicate_check(
                    source=source,
                    text=item["text"],
                    customer_id=customer_id,
                    meta=meta,
                    created_at=created_at
                )

                if is_duplicate:
                    duplicates.append({
                        "index": i,
                        "id": str(feedback.id),
                        "existing_created_at": feedback.created_at.isoformat()
                    })
                else:
                    created.append({
                        "index": i,
                        "id": str(feedback.id),
                        "created_at": feedback.created_at.isoformat()
                    })

            except Exception as e:
                errors.append({
                    "index": i,
                    "error": str(e)
                })

        return {
            "created": created,
            "duplicates": duplicates,
            "errors": errors,
            "summary": {
                "total_processed": len(feedback_items),
                "created_count": len(created),
                "duplicate_count": len(duplicates),
                "error_count": len(errors)
            }
        }

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
