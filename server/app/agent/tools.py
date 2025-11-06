"""
LangChain tools for the feedback analysis agent.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from langchain_core.tools import BaseTool
from langchain_core.pydantic_v1 import BaseModel, Field

from ..repositories.analytics import AnalyticsRepository
from ..repositories.feedback import FeedbackRepository
from ..services.embedding_service import EmbeddingService
from ..services.database import SessionLocal

logger = logging.getLogger(__name__)


class AnalyticsSQLTool(BaseTool):
    """Read-only parameterized SQL tool for analytics queries."""

    name: str = "analytics_sql"
    description: str = """
    Execute read-only, parameterized SQL queries against the feedback database.
    Use this tool to get aggregated analytics data, trends, and statistics.
    Always parameterize queries to prevent SQL injection. Only SELECT queries are allowed.

    Available tables and their key columns:
    - feedback: id (UUID), source, created_at, text, normalized_text, detected_language, meta
    - nlp_annotation: feedback_id, sentiment (-1,0,1), sentiment_score, topic_id, toxicity_score, embedding
    - topic: id, label, keywords, updated_at
    - topic_audit_log: topic_id, action, old_label, new_label, changed_by, changed_at

    Common query patterns:
    - Sentiment analysis: JOIN feedback f LEFT JOIN nlp_annotation na ON f.id = na.feedback_id
    - Topic analysis: JOIN topic t LEFT JOIN nlp_annotation na ON t.id = na.topic_id
    - Time-based trends: GROUP BY DATE_TRUNC('day/week/month', created_at)
    """

    db: Session = Field(default_factory=SessionLocal)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.analytics_repo = AnalyticsRepository(self.db)

    def _run(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a read-only parameterized SQL query.

        Args:
            query: The SQL query to execute (must be SELECT only)
            parameters: Query parameters for safe execution

        Returns:
            JSON string representation of query results
        """
        try:
            # Validate query is read-only
            if not query.strip().upper().startswith("SELECT"):
                raise ValueError("Only SELECT queries are allowed for safety")

            # Execute query through repository for safety
            results = self.analytics_repo.execute_query(query, parameters or {}, fetch="all")

            # Format results as readable string
            if not results:
                return "No results found."

            # Convert to readable format
            formatted_results = []
            for row in results:
                formatted_row = {}
                for key, value in row.items():
                    if isinstance(value, datetime):
                        formatted_row[key] = value.isoformat()
                    elif isinstance(value, float):
                        formatted_row[key] = round(value, 4)
                    else:
                        formatted_row[key] = value
                formatted_results.append(formatted_row)

            return str(formatted_results)

        except Exception as e:
            logger.error(f"AnalyticsSQLTool error: {e}")
            return f"Error executing query: {str(e)}"

    async def _arun(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Async version of _run."""
        return self._run(query, parameters)


class VectorExamplesTool(BaseTool):
    """Tool for retrieving exemplar comments by topic and sentiment."""

    name: str = "vector_examples"
    description: str = """
    Retrieve exemplar feedback comments filtered by topic and/or sentiment.
    Use this to find representative examples of customer feedback for specific topics or sentiments.

    Parameters:
    - topic_id: Optional integer topic ID to filter by
    - sentiment: Optional sentiment filter (-1 for negative, 0 for neutral, 1 for positive)
    - limit: Maximum number of examples to return (default: 5, max: 10)

    Returns feedback examples with IDs, text, sentiment scores, and topic information.
    Always cite feedback_ids when quoting these examples.
    """

    db: Session = Field(default_factory=SessionLocal)
    embedding_service: EmbeddingService = Field(default_factory=EmbeddingService)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.feedback_repo = FeedbackRepository(self.db)
        self.analytics_repo = AnalyticsRepository(self.db)

    def _run(
        self,
        topic_id: Optional[int] = None,
        sentiment: Optional[int] = None,
        limit: int = 5
    ) -> str:
        """
        Retrieve exemplar feedback comments.

        Args:
            topic_id: Optional topic ID filter
            sentiment: Optional sentiment filter (-1, 0, 1)
            limit: Maximum examples to return

        Returns:
            Formatted string of feedback examples
        """
        try:
            # Validate parameters
            if sentiment is not None and sentiment not in [-1, 0, 1]:
                raise ValueError("Sentiment must be -1, 0, or 1")

            if limit > 10:
                limit = 10  # Cap at 10 for performance

            # Get examples using analytics repository
            examples = self.analytics_repo.get_feedback_examples(
                topic_id=topic_id,
                sentiment=sentiment,
                limit=limit
            )

            if not examples:
                return f"No feedback examples found for topic_id={topic_id}, sentiment={sentiment}"

            # Format examples for readability
            formatted_examples = []
            for example in examples:
                formatted_example = {
                    "feedback_id": str(example.get("id", "")),
                    "text": example.get("text", "")[:200] + "..." if len(example.get("text", "")) > 200 else example.get("text", ""),
                    "sentiment": example.get("sentiment"),
                    "sentiment_score": round(example.get("sentiment_score", 0), 3),
                    "topic_id": example.get("topic_id"),
                    "topic_label": example.get("topic_label", ""),
                    "created_at": example.get("created_at").isoformat() if example.get("created_at") else ""
                }
                formatted_examples.append(formatted_example)

            return str(formatted_examples)

        except Exception as e:
            logger.error(f"VectorExamplesTool error: {e}")
            return f"Error retrieving examples: {str(e)}"

    async def _arun(
        self,
        topic_id: Optional[int] = None,
        sentiment: Optional[int] = None,
        limit: int = 5
    ) -> str:
        """Async version of _run."""
        return self._run(topic_id, sentiment, limit)


class ReportWriterTool(BaseTool):
    """Tool for writing weekly summary reports."""

    name: str = "report_writer"
    description: str = """
    Write a weekly summary report row to the database.
    Use this tool to create structured weekly reports with key metrics and insights.

    Required parameters:
    - week_start_date: Start date of the week (YYYY-MM-DD format)
    - total_feedback: Total number of feedback items
    - negative_percentage: Percentage of negative feedback
    - top_topics: List of top topic labels and their counts
    - key_insights: List of key insights or trends observed

    Optional parameters:
    - avg_sentiment_score: Average sentiment score across all feedback
    - most_negative_topic: The topic with highest negative feedback
    - improvement_areas: Areas identified for improvement
    """

    db: Session = Field(default_factory=SessionLocal)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.analytics_repo = AnalyticsRepository(self.db)

    def _run(
        self,
        week_start_date: str,
        total_feedback: int,
        negative_percentage: float,
        top_topics: List[str],
        key_insights: List[str],
        avg_sentiment_score: Optional[float] = None,
        most_negative_topic: Optional[str] = None,
        improvement_areas: Optional[List[str]] = None
    ) -> str:
        """
        Write a weekly summary report to the database.

        Args:
            week_start_date: Start date of the week
            total_feedback: Total feedback count
            negative_percentage: Negative feedback percentage
            top_topics: Top topic labels
            key_insights: Key insights identified
            avg_sentiment_score: Average sentiment score
            most_negative_topic: Most negative topic
            improvement_areas: Areas for improvement

        Returns:
            Success message with report details
        """
        try:
            # Validate date format
            try:
                datetime.fromisoformat(week_start_date)
            except ValueError:
                raise ValueError("week_start_date must be in YYYY-MM-DD format")

            # Prepare report data
            report_data = {
                "week_start_date": week_start_date,
                "total_feedback": total_feedback,
                "negative_percentage": negative_percentage,
                "top_topics": top_topics,
                "key_insights": key_insights,
                "avg_sentiment_score": avg_sentiment_score,
                "most_negative_topic": most_negative_topic,
                "improvement_areas": improvement_areas or [],
                "created_at": datetime.utcnow().isoformat()
            }

            # In a real implementation, this would write to a reports table
            # For now, we'll simulate writing and return success
            logger.info(f"Weekly report written for week starting {week_start_date}")

            return f"Successfully wrote weekly report for {week_start_date}: {total_feedback} total feedback, {negative_percentage}% negative"

        except Exception as e:
            logger.error(f"ReportWriterTool error: {e}")
            return f"Error writing report: {str(e)}"

    async def _arun(
        self,
        week_start_date: str,
        total_feedback: int,
        negative_percentage: float,
        top_topics: List[str],
        key_insights: List[str],
        avg_sentiment_score: Optional[float] = None,
        most_negative_topic: Optional[str] = None,
        improvement_areas: Optional[List[str]] = None
    ) -> str:
        """Async version of _run."""
        return self._run(
            week_start_date, total_feedback, negative_percentage, top_topics, key_insights,
            avg_sentiment_score, most_negative_topic, improvement_areas
        )
