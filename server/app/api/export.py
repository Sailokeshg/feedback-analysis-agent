import csv
import io
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import time

from ..services.database import get_db
from ..logging import get_logger
from ..metrics import increment_http_requests, observe_http_request_duration

router = APIRouter()
log = get_logger("export_api")


def generate_csv_rows(db: Session, query: str, params: dict = None):
    """Generator function to yield CSV rows for streaming"""
    if params is None:
        params = {}

    try:
        result = db.execute(text(query), params)
        columns = result.keys()

        # Yield header row
        yield columns

        # Yield data rows
        for row in result:
            yield row

    except Exception as e:
        log.error(f"Error executing export query: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


def create_csv_stream(generator):
    """Convert generator to CSV stream"""
    output = io.StringIO()
    writer = None

    for row in generator:
        if writer is None:
            # First row is headers
            writer = csv.writer(output)
            writer.writerow(row)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
        else:
            # Data rows
            writer.writerow(row)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)


@router.get("/export.csv")
async def export_feedback_csv(
    source: Optional[str] = Query(None, description="Filter by source"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    sentiment_min: Optional[float] = Query(None, description="Minimum sentiment score (0-1)"),
    sentiment_max: Optional[float] = Query(None, description="Maximum sentiment score (0-1)"),
    db: Session = Depends(get_db)
):
    """
    Export feedback data as CSV with optional filters.

    Supports streaming for large datasets.
    """
    start_time = time.time()

    try:
        # Build query with filters
        base_query = """
        SELECT
            f.id,
            f.text,
            f.source,
            f.customer_id,
            f.sentiment_score,
            f.created_at,
            f.updated_at,
            -- Include topic information if available
            COALESCE(t.label, '') as primary_topic,
            COALESCE(t.keywords, '') as topic_keywords
        FROM feedback f
        LEFT JOIN topic t ON f.id = (
            SELECT ft.feedback_id
            FROM feedback_topic ft
            WHERE ft.feedback_id = f.id
            LIMIT 1
        )
        WHERE 1=1
        """

        params = {}

        if source:
            base_query += " AND f.source = :source"
            params["source"] = source

        if customer_id:
            base_query += " AND f.customer_id = :customer_id"
            params["customer_id"] = customer_id

        if start_date:
            base_query += " AND DATE(f.created_at) >= :start_date"
            params["start_date"] = start_date

        if end_date:
            base_query += " AND DATE(f.created_at) <= :end_date"
            params["end_date"] = end_date

        if sentiment_min is not None:
            base_query += " AND f.sentiment_score >= :sentiment_min"
            params["sentiment_min"] = sentiment_min

        if sentiment_max is not None:
            base_query += " AND f.sentiment_score <= :sentiment_max"
            params["sentiment_max"] = sentiment_max

        base_query += " ORDER BY f.created_at DESC"

        log.info("Starting CSV export", extra={
            "filters": {
                "source": source,
                "customer_id": customer_id,
                "date_range": f"{start_date} to {end_date}" if start_date or end_date else None,
                "sentiment_range": f"{sentiment_min} to {sentiment_max}" if sentiment_min is not None or sentiment_max is not None else None
            }
        })

        # Create streaming response
        def generate_csv():
            yield from create_csv_stream(generate_csv_rows(db, base_query, params))

        response = StreamingResponse(
            generate_csv(),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=feedback_export.csv",
                "Cache-Control": "no-cache"
            }
        )

        # Record metrics
        increment_http_requests("export_csv", "GET", 200)
        observe_http_request_duration("export_csv", time.time() - start_time)

        return response

    except Exception as e:
        log.error(f"Export failed: {e}")
        increment_http_requests("export_csv", "GET", 500)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/export/topics.csv")
async def export_topics_csv(
    min_feedback_count: Optional[int] = Query(1, description="Minimum feedback count for topics"),
    db: Session = Depends(get_db)
):
    """
    Export topics data as CSV.
    """
    start_time = time.time()

    try:
        query = """
        SELECT
            t.id,
            t.label,
            t.keywords,
            t.created_at,
            t.updated_at,
            COUNT(ft.feedback_id) as feedback_count,
            AVG(f.sentiment_score) as avg_sentiment
        FROM topic t
        LEFT JOIN feedback_topic ft ON t.id = ft.topic_id
        LEFT JOIN feedback f ON ft.feedback_id = f.id
        GROUP BY t.id, t.label, t.keywords, t.created_at, t.updated_at
        HAVING COUNT(ft.feedback_id) >= :min_feedback_count
        ORDER BY feedback_count DESC, t.created_at DESC
        """

        params = {"min_feedback_count": min_feedback_count}

        log.info("Starting topics CSV export", extra={
            "min_feedback_count": min_feedback_count
        })

        def generate_csv():
            yield from create_csv_stream(generate_csv_rows(db, query, params))

        response = StreamingResponse(
            generate_csv(),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=topics_export.csv",
                "Cache-Control": "no-cache"
            }
        )

        increment_http_requests("export_topics_csv", "GET", 200)
        observe_http_request_duration("export_topics_csv", time.time() - start_time)

        return response

    except Exception as e:
        log.error(f"Topics export failed: {e}")
        increment_http_requests("export_topics_csv", "GET", 500)
        raise HTTPException(status_code=500, detail=f"Topics export failed: {str(e)}")


@router.get("/export/analytics.csv")
async def export_analytics_csv(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Export analytics data (daily aggregates) as CSV.
    """
    start_time = time.time()

    try:
        query = """
        SELECT
            date,
            total_feedback,
            positive_feedback,
            negative_feedback,
            neutral_feedback,
            avg_sentiment,
            unique_customers,
            top_sources
        FROM daily_feedback_aggregates
        WHERE 1=1
        """

        params = {}

        if start_date:
            query += " AND date >= :start_date"
            params["start_date"] = start_date

        if end_date:
            query += " AND date <= :end_date"
            params["end_date"] = end_date

        query += " ORDER BY date DESC"

        log.info("Starting analytics CSV export", extra={
            "date_range": f"{start_date} to {end_date}" if start_date or end_date else None
        })

        def generate_csv():
            yield from create_csv_stream(generate_csv_rows(db, query, params))

        response = StreamingResponse(
            generate_csv(),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=analytics_export.csv",
                "Cache-Control": "no-cache"
            }
        )

        increment_http_requests("export_analytics_csv", "GET", 200)
        observe_http_request_duration("export_analytics_csv", time.time() - start_time)

        return response

    except Exception as e:
        log.error(f"Analytics export failed: {e}")
        increment_http_requests("export_analytics_csv", "GET", 500)
        raise HTTPException(status_code=500, detail=f"Analytics export failed: {str(e)}")
