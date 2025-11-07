"""
Topic repository for CRUD operations on topics with audit logging.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .base import BaseRepository
from ..models import Topic, TopicAuditLog
from ..logging import get_logger

logger = get_logger("topic_repository")


class TopicRepository(BaseRepository[Topic]):
    """Repository for topic CRUD operations with audit logging."""

    def __init__(self, session: Session):
        super().__init__(session)

    def get_topic_by_id(self, topic_id: int) -> Optional[Topic]:
        """Get topic by ID."""
        return self.session.query(Topic).filter(Topic.id == topic_id).first()

    def update_topic_label(
        self,
        topic_id: int,
        new_label: str,
        new_keywords: List[str],
        changed_by: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Topic:
        """
        Update topic label and keywords with audit logging.

        Args:
            topic_id: ID of the topic to update
            new_label: New label for the topic
            new_keywords: New keywords for the topic
            changed_by: User identifier making the change
            ip_address: IP address of the user
            user_agent: User agent string

        Returns:
            Updated topic object

        Raises:
            ValueError: If topic not found
        """
        topic = self.get_topic_by_id(topic_id)
        if not topic:
            raise ValueError(f"Topic with ID {topic_id} not found")

        # Store old values for audit log
        old_label = topic.label
        old_keywords = topic.keywords.copy() if topic.keywords else []

        # Update topic
        topic.label = new_label
        topic.keywords = new_keywords
        topic.updated_at = datetime.utcnow()

        # Create audit log entry
        audit_log = TopicAuditLog(
            topic_id=topic_id,
            action="update",
            old_label=old_label,
            new_label=new_label,
            old_keywords=old_keywords,
            new_keywords=new_keywords,
            changed_by=changed_by,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.session.add(audit_log)
        self.session.commit()
        self.session.refresh(topic)

        return topic

    def get_topic_audit_history(self, topic_id: int) -> List[Dict[str, Any]]:
        """Get audit history for a topic."""
        audit_logs = (
            self.session.query(TopicAuditLog)
            .filter(TopicAuditLog.topic_id == topic_id)
            .order_by(TopicAuditLog.changed_at.desc())
            .all()
        )

        return [
            {
                "id": log.id,
                "action": log.action,
                "old_label": log.old_label,
                "new_label": log.new_label,
                "old_keywords": log.old_keywords,
                "new_keywords": log.new_keywords,
                "changed_by": log.changed_by,
                "changed_at": log.changed_at.isoformat(),
                "ip_address": log.ip_address,
                "user_agent": log.user_agent
            }
            for log in audit_logs
        ]

    def get_recent_audit_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent audit logs across all topics."""
        audit_logs = (
            self.session.query(TopicAuditLog, Topic.label)
            .join(Topic, TopicAuditLog.topic_id == Topic.id)
            .order_by(TopicAuditLog.changed_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": log.id,
                "topic_id": log.topic_id,
                "topic_label": topic_label,
                "action": log.action,
                "old_label": log.old_label,
                "new_label": log.new_label,
                "old_keywords": log.old_keywords,
                "new_keywords": log.new_keywords,
                "changed_by": log.changed_by,
                "changed_at": log.changed_at.isoformat(),
                "ip_address": log.ip_address,
                "user_agent": log.user_agent
            }
            for log, topic_label in audit_logs
        ]

    def get_or_create_topic(self, label: str, keywords: List[str], changed_by: str = "system") -> Topic:
        """
        Get existing topic by label or create new one.

        Args:
            label: Topic label
            keywords: Topic keywords
            changed_by: User/system identifier

        Returns:
            Topic object
        """
        # Try to find existing topic with same label
        existing_topic = (
            self.session.query(Topic)
            .filter(Topic.label == label)
            .first()
        )

        if existing_topic:
            # Update keywords if they differ
            if set(existing_topic.keywords or []) != set(keywords):
                return self.update_topic_label(
                    existing_topic.id,
                    existing_topic.label,
                    keywords,
                    changed_by
                )
            return existing_topic

        # Create new topic
        topic = Topic(
            label=label,
            keywords=keywords
        )

        self.session.add(topic)
        self.session.commit()
        self.session.refresh(topic)

        logger.info(f"Created new topic: {label} with {len(keywords)} keywords")
        return topic

    def bulk_create_topics(self, topic_data: List[Dict[str, Any]], changed_by: str = "system") -> List[Topic]:
        """
        Bulk create or update topics.

        Args:
            topic_data: List of dicts with 'label' and 'keywords' keys
            changed_by: User/system identifier

        Returns:
            List of created/updated topic objects
        """
        topics = []
        for data in topic_data:
            topic = self.get_or_create_topic(
                data['label'],
                data['keywords'],
                changed_by
            )
            topics.append(topic)

        return topics

    def reassign_feedback_to_topic(
        self,
        feedback_id: str,
        new_topic_id: int,
        changed_by: str,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reassign feedback comment to a different topic with audit logging.

        Args:
            feedback_id: UUID of the feedback to reassign
            new_topic_id: ID of the new topic
            changed_by: User identifier making the change
            reason: Optional reason for reassignment
            ip_address: IP address of the user
            user_agent: User agent string

        Returns:
            Dict with reassignment details

        Raises:
            ValueError: If feedback or topic not found
        """
        from ..models import NLPAnnotation

        # Verify new topic exists
        new_topic = self.get_topic_by_id(new_topic_id)
        if not new_topic:
            raise ValueError(f"Topic with ID {new_topic_id} not found")

        # Get current annotation for this feedback
        annotation = (
            self.session.query(NLPAnnotation)
            .filter(NLPAnnotation.feedback_id == feedback_id)
            .first()
        )

        if not annotation:
            raise ValueError(f"No annotation found for feedback {feedback_id}")

        # Store old topic info
        old_topic_id = annotation.topic_id
        old_topic_label = None
        if old_topic_id:
            old_topic = self.get_topic_by_id(old_topic_id)
            old_topic_label = old_topic.label if old_topic else None

        # Update annotation
        annotation.topic_id = new_topic_id

        # Create audit log entry for the reassignment
        audit_log = TopicAuditLog(
            topic_id=new_topic_id,
            action="reassign_feedback",
            changed_by=changed_by,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Add metadata about the reassignment
        audit_log.old_label = f"Feedback {feedback_id} reassigned"
        audit_log.new_label = f"From topic {old_topic_id} ({old_topic_label}) to topic {new_topic_id} ({new_topic.label})"
        if reason:
            audit_log.new_label += f" - Reason: {reason}"

        self.session.add(audit_log)
        self.session.commit()

        return {
            "feedback_id": feedback_id,
            "old_topic_id": old_topic_id,
            "new_topic_id": new_topic_id,
            "old_topic_label": old_topic_label,
            "new_topic_label": new_topic.label,
            "reason": reason,
            "reassigned_by": changed_by,
            "reassigned_at": audit_log.changed_at.isoformat()
        }
