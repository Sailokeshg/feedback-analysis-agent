"""
Read-only analytics repository with whitelisted operations.
Provides safe, efficient analytics queries using materialized views and optimized queries.
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from .base import BaseRepository, DateFilter, PaginationParams

class AnalyticsRepository(BaseRepository):
    """
    Read-only analytics repository with whitelisted operations.
    Only allows safe, pre-defined analytics queries.
    """

    # Whitelisted operations - only these queries are allowed
    ALLOWED_QUERIES = {
        "sentiment_trends",
        "topic_distribution",
        "daily_aggregates",
        "customer_stats",
        "source_stats",
        "toxicity_analysis",
        "feedback_volume_trends"
    }

    def __init__(self, session: Session):
        super().__init__(session)

    def get_sentiment_trends(
        self,
        date_filter: Optional[DateFilter] = None,
        group_by: str = "day"  # day, week, month
    ) -> List[Dict[str, Any]]:
        """
        Get sentiment trends over time.

        Args:
            date_filter: Optional date range filter
            group_by: Time grouping (day, week, month)

        Returns:
            List of sentiment trends by time period
        """
        if group_by not in ["day", "week", "month"]:
            raise ValueError("group_by must be 'day', 'week', or 'month'")

        # Define date truncation based on group_by
        date_trunc = {
            "day": "DATE(created_at)",
            "week": "DATE_TRUNC('week', created_at)",
            "month": "DATE_TRUNC('month', created_at)"
        }[group_by]

        query = f"""
        SELECT
            {date_trunc} as period,
            COUNT(*) as total_feedback,
            COUNT(CASE WHEN sentiment = 1 THEN 1 END) as positive_count,
            COUNT(CASE WHEN sentiment = 0 THEN 1 END) as neutral_count,
            COUNT(CASE WHEN sentiment = -1 THEN 1 END) as negative_count,
            ROUND(AVG(sentiment_score)::numeric, 4) as avg_sentiment_score,
            ROUND(AVG(toxicity_score)::numeric, 4) as avg_toxicity_score
        FROM feedback f
        LEFT JOIN nlp_annotation na ON f.id = na.feedback_id
        """

        params = {}

        # Apply date filter
        if date_filter:
            date_condition = date_filter.to_sql_condition()
            if date_condition:
                query += f" WHERE {date_condition}"
                params.update(date_filter.to_params())

        query += f" GROUP BY {date_trunc} ORDER BY period DESC"

        return self.execute_query(query, params, fetch="all")

    def get_topic_distribution(
        self,
        date_filter: Optional[DateFilter] = None,
        min_feedback_count: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get topic distribution with sentiment analysis.

        Args:
            date_filter: Optional date range filter
            min_feedback_count: Minimum feedback count per topic

        Returns:
            List of topics with sentiment distribution
        """
        query = """
        SELECT
            t.id,
            t.label,
            t.keywords,
            COUNT(f.id) as feedback_count,
            COUNT(CASE WHEN na.sentiment = 1 THEN 1 END) as positive_count,
            COUNT(CASE WHEN na.sentiment = 0 THEN 1 END) as neutral_count,
            COUNT(CASE WHEN na.sentiment = -1 THEN 1 END) as negative_count,
            ROUND(AVG(na.sentiment_score)::numeric, 4) as avg_sentiment_score,
            ROUND(AVG(na.toxicity_score)::numeric, 4) as avg_toxicity_score,
            MAX(t.updated_at) as last_updated
        FROM topic t
        LEFT JOIN nlp_annotation na ON t.id = na.topic_id
        LEFT JOIN feedback f ON na.feedback_id = f.id
        """

        params = {"min_count": min_feedback_count}

        # Apply date filter
        if date_filter:
            date_condition = date_filter.to_sql_condition()
            if date_condition:
                query += f" WHERE {date_condition}"
                params.update(date_filter.to_params())

        query += """
        GROUP BY t.id, t.label, t.keywords
        HAVING COUNT(f.id) >= :min_count
        ORDER BY feedback_count DESC, avg_sentiment_score DESC
        """

        return self.execute_query(query, params, fetch="all")

    def get_daily_aggregates(
        self,
        date_filter: Optional[DateFilter] = None,
        pagination: Optional[PaginationParams] = None
    ) -> Dict[str, Any]:
        """
        Get daily feedback aggregates from materialized view.

        Args:
            date_filter: Optional date range filter
            pagination: Optional pagination parameters

        Returns:
            Paginated daily aggregates
        """
        query = """
        SELECT
            date,
            total_feedback,
            positive_count,
            neutral_count,
            negative_count,
            avg_sentiment_score,
            avg_toxicity_score,
            unique_customers,
            unique_topics
        FROM daily_feedback_aggregates
        """

        params = {}

        # Apply date filter
        if date_filter:
            date_condition = date_filter.to_sql_condition()
            if date_condition:
                query += f" WHERE {date_condition}"
                params.update(date_filter.to_params())

        query += " ORDER BY date DESC"

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

    def get_customer_stats(
        self,
        date_filter: Optional[DateFilter] = None,
        min_feedback_count: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get customer feedback statistics.

        Args:
            date_filter: Optional date range filter
            min_feedback_count: Minimum feedback count per customer

        Returns:
            List of customer statistics
        """
        query = """
        SELECT
            f.customer_id,
            COUNT(f.id) as feedback_count,
            COUNT(DISTINCT f.source) as sources_used,
            MIN(f.created_at) as first_feedback_date,
            MAX(f.created_at) as last_feedback_date,
            COUNT(CASE WHEN na.sentiment = 1 THEN 1 END) as positive_count,
            COUNT(CASE WHEN na.sentiment = 0 THEN 1 END) as neutral_count,
            COUNT(CASE WHEN na.sentiment = -1 THEN 1 END) as negative_count,
            ROUND(AVG(na.sentiment_score)::numeric, 4) as avg_sentiment_score,
            ROUND(AVG(na.toxicity_score)::numeric, 4) as avg_toxicity_score
        FROM feedback f
        LEFT JOIN nlp_annotation na ON f.id = na.feedback_id
        WHERE f.customer_id IS NOT NULL
        """

        params = {"min_count": min_feedback_count}

        # Apply date filter
        if date_filter:
            date_condition = date_filter.to_sql_condition()
            if date_condition:
                query += f" AND {date_condition}"
                params.update(date_filter.to_params())

        query += """
        GROUP BY f.customer_id
        HAVING COUNT(f.id) >= :min_count
        ORDER BY feedback_count DESC, last_feedback_date DESC
        """

        return self.execute_query(query, params, fetch="all")

    def get_source_stats(
        self,
        date_filter: Optional[DateFilter] = None
    ) -> List[Dict[str, Any]]:
        """
        Get feedback statistics by source.

        Args:
            date_filter: Optional date range filter

        Returns:
            List of source statistics
        """
        query = """
        SELECT
            f.source,
            COUNT(f.id) as feedback_count,
            COUNT(DISTINCT f.customer_id) as unique_customers,
            COUNT(CASE WHEN na.sentiment = 1 THEN 1 END) as positive_count,
            COUNT(CASE WHEN na.sentiment = 0 THEN 1 END) as neutral_count,
            COUNT(CASE WHEN na.sentiment = -1 THEN 1 END) as negative_count,
            ROUND(AVG(na.sentiment_score)::numeric, 4) as avg_sentiment_score,
            ROUND(AVG(na.toxicity_score)::numeric, 4) as avg_toxicity_score
        FROM feedback f
        LEFT JOIN nlp_annotation na ON f.id = na.feedback_id
        """

        params = {}

        # Apply date filter
        if date_filter:
            date_condition = date_filter.to_sql_condition()
            if date_condition:
                query += f" WHERE {date_condition}"
                params.update(date_filter.to_params())

        query += """
        GROUP BY f.source
        ORDER BY feedback_count DESC
        """

        return self.execute_query(query, params, fetch="all")

    def get_toxicity_analysis(
        self,
        date_filter: Optional[DateFilter] = None,
        toxicity_threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Get toxicity analysis statistics.

        Args:
            date_filter: Optional date range filter
            toxicity_threshold: Threshold for considering content toxic

        Returns:
            Toxicity analysis summary
        """
        query = """
        SELECT
            COUNT(*) as total_analyzed,
            COUNT(CASE WHEN na.toxicity_score >= :threshold THEN 1 END) as toxic_count,
            COUNT(CASE WHEN na.toxicity_score < :threshold THEN 1 END) as non_toxic_count,
            ROUND(AVG(na.toxicity_score)::numeric, 4) as avg_toxicity_score,
            ROUND(MIN(na.toxicity_score)::numeric, 4) as min_toxicity_score,
            ROUND(MAX(na.toxicity_score)::numeric, 4) as max_toxicity_score,
            ROUND(STDDEV(na.toxicity_score)::numeric, 4) as toxicity_stddev
        FROM feedback f
        LEFT JOIN nlp_annotation na ON f.id = na.feedback_id
        WHERE na.toxicity_score IS NOT NULL
        """

        params = {"threshold": toxicity_threshold}

        # Apply date filter
        if date_filter:
            date_condition = date_filter.to_sql_condition()
            if date_condition:
                query += f" AND {date_condition}"
                params.update(date_filter.to_params())

        result = self.execute_query(query, params, fetch="one")
        return result or {}

    def get_feedback_volume_trends(
        self,
        date_filter: Optional[DateFilter] = None,
        group_by: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        Get feedback volume trends over time.

        Args:
            date_filter: Optional date range filter
            group_by: Time grouping (day, week, month)

        Returns:
            List of volume trends by time period
        """
        if group_by not in ["day", "week", "month"]:
            raise ValueError("group_by must be 'day', 'week', or 'month'")

        date_trunc = {
            "day": "DATE(created_at)",
            "week": "DATE_TRUNC('week', created_at)",
            "month": "DATE_TRUNC('month', created_at)"
        }[group_by]

        query = f"""
        SELECT
            {date_trunc} as period,
            COUNT(*) as total_feedback,
            COUNT(DISTINCT f.customer_id) as unique_customers,
            COUNT(DISTINCT f.source) as sources_used,
            COUNT(CASE WHEN na.sentiment IS NOT NULL THEN 1 END) as analyzed_feedback,
            ROUND(
                COUNT(CASE WHEN na.sentiment IS NOT NULL THEN 1 END)::numeric /
                NULLIF(COUNT(*), 0) * 100, 2
            ) as analysis_completion_rate
        FROM feedback f
        LEFT JOIN nlp_annotation na ON f.id = na.feedback_id
        """

        params = {}

        # Apply date filter
        if date_filter:
            date_condition = date_filter.to_sql_condition()
            if date_condition:
                query += f" WHERE {date_condition}"
                params.update(date_filter.to_params())

        query += f" GROUP BY {date_trunc} ORDER BY period DESC"

        return self.execute_query(query, params, fetch="all")

    def execute_whitelisted_query(
        self,
        operation: str,
        **kwargs
    ) -> Any:
        """
        Execute only whitelisted analytics operations.

        Args:
            operation: Name of the whitelisted operation
            **kwargs: Parameters for the operation

        Returns:
            Operation results

        Raises:
            ValueError: If operation is not whitelisted
        """
        if operation not in self.ALLOWED_QUERIES:
            raise ValueError(
                f"Operation '{operation}' is not whitelisted. "
                f"Allowed operations: {sorted(self.ALLOWED_QUERIES)}"
            )

        method = getattr(self, f"get_{operation}", None)
        if not method:
            raise ValueError(f"Method for operation '{operation}' not found")

        return method(**kwargs)
