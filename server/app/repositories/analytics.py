"""
Read-only analytics repository with whitelisted operations.
Provides safe, efficient analytics queries using materialized views and optimized queries.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
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

    def get_analytics_summary(
        self,
        date_filter: Optional[DateFilter] = None
    ) -> Dict[str, Any]:
        """
        Get analytics summary with totals, negative percentage, and daily trend.

        Args:
            date_filter: Optional date range filter

        Returns:
            Summary statistics including totals, negative percentage, and daily trend
        """
        # Get overall totals
        totals_query = """
        SELECT
            COUNT(*) as total_feedback,
            COUNT(CASE WHEN na.sentiment = -1 THEN 1 END) as negative_count,
            COUNT(CASE WHEN na.sentiment = 0 THEN 1 END) as neutral_count,
            COUNT(CASE WHEN na.sentiment = 1 THEN 1 END) as positive_count,
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
                totals_query += f" WHERE {date_condition}"
                params.update(date_filter.to_params())

        totals = self.execute_query(totals_query, params, fetch="one") or {}

        # Calculate negative percentage
        total_feedback = totals.get('total_feedback', 0)
        negative_count = totals.get('negative_count', 0)
        negative_percentage = round((negative_count / total_feedback * 100), 2) if total_feedback > 0 else 0

        # Get daily trend (last 30 days)
        trend_query = """
        SELECT
            DATE(f.created_at) as date,
            COUNT(*) as total_feedback,
            COUNT(CASE WHEN na.sentiment = -1 THEN 1 END) as negative_count,
            COUNT(CASE WHEN na.sentiment = 0 THEN 1 END) as neutral_count,
            COUNT(CASE WHEN na.sentiment = 1 THEN 1 END) as positive_count,
            ROUND(AVG(na.sentiment_score)::numeric, 4) as avg_sentiment_score
        FROM feedback f
        LEFT JOIN nlp_annotation na ON f.id = na.feedback_id
        WHERE f.created_at >= CURRENT_DATE - INTERVAL '30 days'
        """

        if date_filter:
            # If date filter is provided, use it for trend too but limit to 30 days max
            trend_date_filter = DateFilter(
                start_date=max(date_filter.start_date, (datetime.now() - timedelta(days=30)).date()) if date_filter.start_date else (datetime.now() - timedelta(days=30)).date(),
                end_date=date_filter.end_date
            )
            trend_condition = trend_date_filter.to_sql_condition()
            if trend_condition:
                trend_query += f" AND {trend_condition}"
                params.update(trend_date_filter.to_params())

        trend_query += " GROUP BY DATE(f.created_at) ORDER BY date DESC"

        daily_trend = self.execute_query(trend_query, params, fetch="all")

        return {
            "total_feedback": total_feedback,
            "negative_count": negative_count,
            "neutral_count": totals.get('neutral_count', 0),
            "positive_count": totals.get('positive_count', 0),
            "negative_percentage": negative_percentage,
            "avg_sentiment_score": totals.get('avg_sentiment_score', 0),
            "avg_toxicity_score": totals.get('avg_toxicity_score', 0),
            "daily_trend": daily_trend
        }

    def get_analytics_topics(
        self,
        date_filter: Optional[DateFilter] = None
    ) -> List[Dict[str, Any]]:
        """
        Get analytics topics with topic_id, label, count, avg_sentiment, and delta_week.

        Args:
            date_filter: Optional date range filter

        Returns:
            List of topics with analytics data
        """
        query = """
        WITH current_period AS (
            SELECT
                t.id,
                t.label,
                COUNT(f.id) as feedback_count,
                ROUND(AVG(na.sentiment_score)::numeric, 4) as avg_sentiment
            FROM topic t
            LEFT JOIN nlp_annotation na ON t.id = na.topic_id
            LEFT JOIN feedback f ON na.feedback_id = f.id
        """

        params = {}

        # Apply date filter to current period
        if date_filter:
            date_condition = date_filter.to_sql_condition()
            if date_condition:
                query += f" WHERE {date_condition}"
                params.update(date_filter.to_params())

        query += """
            GROUP BY t.id, t.label
        ),
        previous_week AS (
            SELECT
                t.id,
                COUNT(f.id) as prev_feedback_count,
                ROUND(AVG(na.sentiment_score)::numeric, 4) as prev_avg_sentiment
            FROM topic t
            LEFT JOIN nlp_annotation na ON t.id = na.topic_id
            LEFT JOIN feedback f ON na.feedback_id = f.id
            WHERE f.created_at >= CURRENT_DATE - INTERVAL '14 days'
            AND f.created_at < CURRENT_DATE - INTERVAL '7 days'
        """

        # Apply same date filter logic but shifted back 7 days for comparison
        if date_filter and date_filter.start_date:
            prev_start = date_filter.start_date - timedelta(days=7)
            prev_end = (date_filter.end_date - timedelta(days=7)) if date_filter.end_date else None
            prev_filter = DateFilter(start_date=prev_start, end_date=prev_end)
            prev_condition = prev_filter.to_sql_condition()
            if prev_condition:
                query += f" AND {prev_condition}"

        query += """
            GROUP BY t.id
        )
        SELECT
            cp.id as topic_id,
            cp.label,
            cp.feedback_count as count,
            cp.avg_sentiment,
            COALESCE(cp.feedback_count - pw.prev_feedback_count, cp.feedback_count) as delta_week
        FROM current_period cp
        LEFT JOIN previous_week pw ON cp.id = pw.id
        WHERE cp.feedback_count > 0
        ORDER BY cp.feedback_count DESC, cp.avg_sentiment DESC
        """

        return self.execute_query(query, params, fetch="all")

    def get_feedback_examples(
        self,
        topic_id: Optional[int] = None,
        sentiment: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get sample feedback comments with filtering by topic and sentiment.

        Args:
            topic_id: Optional topic ID filter
            sentiment: Optional sentiment filter (-1, 0, 1)
            limit: Maximum number of examples to return

        Returns:
            List of feedback examples with IDs and text
        """
        query = """
        SELECT
            f.id,
            f.text,
            f.created_at,
            na.sentiment,
            na.sentiment_score,
            na.toxicity_score,
            t.id as topic_id,
            t.label as topic_label
        FROM feedback f
        LEFT JOIN nlp_annotation na ON f.id = na.feedback_id
        LEFT JOIN topic t ON na.topic_id = t.id
        """

        params = {"limit": min(limit, 50)}  # Cap at 50 for performance

        conditions = []

        if topic_id is not None:
            conditions.append("na.topic_id = :topic_id")
            params["topic_id"] = topic_id

        if sentiment is not None:
            if sentiment not in [-1, 0, 1]:
                raise ValueError("Sentiment must be -1, 0, or 1")
            conditions.append("na.sentiment = :sentiment")
            params["sentiment"] = sentiment

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY f.created_at DESC LIMIT :limit"

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
