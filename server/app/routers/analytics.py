"""
Analytics router for data analysis and reporting operations.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..services.database import get_db
from ..services.cache_service import cache_service
from ..repositories import AnalyticsRepository, DateFilter, PaginationParams

router = APIRouter()

# Include existing topics and trends functionality
from ..api import topics, trends

# Re-export the endpoints with the analytics prefix
@router.get("/sentiment-trends")
async def get_sentiment_trends(
    group_by: str = Query("day", description="Time grouping (day, week, month)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get sentiment trends over time"""
    try:
        repo = AnalyticsRepository(db)

        # Create date filter if provided
        date_filter = DateFilter(
            start_date=start_date,
            end_date=end_date
        ) if start_date or end_date else None

        # Get sentiment trends
        result = repo.get_sentiment_trends(
            date_filter=date_filter,
            group_by=group_by
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sentiment trends: {str(e)}")

@router.get("/volume-trends")
async def get_volume_trends(
    group_by: str = Query("day", description="Time grouping (day, week, month)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get feedback volume trends over time"""
    try:
        repo = AnalyticsRepository(db)

        # Create date filter if provided
        date_filter = DateFilter(
            start_date=start_date,
            end_date=end_date
        ) if start_date or end_date else None

        # Get volume trends
        result = repo.get_feedback_volume_trends(
            date_filter=date_filter,
            group_by=group_by
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch volume trends: {str(e)}")

@router.get("/daily-aggregates")
async def get_daily_aggregates(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(30, ge=1, le=365, description="Days per page (max 365)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get daily feedback aggregates"""
    try:
        repo = AnalyticsRepository(db)

        # Create pagination and date filter
        pagination = PaginationParams(page=page, page_size=page_size, max_page_size=365)
        date_filter = DateFilter(
            start_date=start_date,
            end_date=end_date
        ) if start_date or end_date else None

        # Get daily aggregates
        result = repo.get_daily_aggregates(
            date_filter=date_filter,
            pagination=pagination
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch daily aggregates: {str(e)}")


@router.get("/customers")
async def get_customer_stats(
    min_feedback_count: int = Query(1, ge=1, description="Minimum feedback count per customer"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get customer feedback statistics"""
    try:
        repo = AnalyticsRepository(db)

        # Create date filter if provided
        date_filter = DateFilter(
            start_date=start_date,
            end_date=end_date
        ) if start_date or end_date else None

        # Get customer stats
        result = repo.get_customer_stats(
            date_filter=date_filter,
            min_feedback_count=min_feedback_count
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch customer stats: {str(e)}")

@router.get("/sources")
async def get_source_stats(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get feedback statistics by source"""
    try:
        repo = AnalyticsRepository(db)

        # Create date filter if provided
        date_filter = DateFilter(
            start_date=start_date,
            end_date=end_date
        ) if start_date or end_date else None

        # Get source stats
        result = repo.get_source_stats(date_filter=date_filter)

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch source stats: {str(e)}")

@router.get("/toxicity")
async def get_toxicity_analysis(
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Toxicity threshold (0.0-1.0)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get toxicity analysis statistics"""
    try:
        repo = AnalyticsRepository(db)

        # Create date filter if provided
        date_filter = DateFilter(
            start_date=start_date,
            end_date=end_date
        ) if start_date or end_date else None

        # Get toxicity analysis
        result = repo.get_toxicity_analysis(
            date_filter=date_filter,
            toxicity_threshold=threshold
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch toxicity analysis: {str(e)}")

@router.get("/summary")
async def get_analytics_summary(
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get analytics summary with totals, negative percentage, and daily trend"""
    try:
        # Create cache key parameters
        cache_params = {"start": start, "end": end}

        # Try to get from cache first
        cached_result = cache_service.get("summary", cache_params)
        if cached_result:
            return cached_result

        repo = AnalyticsRepository(db)

        # Create date filter if provided
        date_filter = DateFilter(
            start_date=start,
            end_date=end
        ) if start or end else None

        # Get analytics summary
        result = repo.get_analytics_summary(date_filter=date_filter)

        # Cache the result for 5 minutes
        cache_service.set("summary", cache_params, result, ttl_seconds=300)

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics summary: {str(e)}")

@router.get("/topics")
async def get_analytics_topics(
    start: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get analytics topics with topic_id, label, count, avg_sentiment, and delta_week"""
    try:
        # Create cache key parameters
        cache_params = {"start": start, "end": end}

        # Try to get from cache first
        cached_result = cache_service.get("topics", cache_params)
        if cached_result:
            return cached_result

        repo = AnalyticsRepository(db)

        # Create date filter if provided
        date_filter = DateFilter(
            start_date=start,
            end_date=end
        ) if start or end else None

        # Get analytics topics
        result = repo.get_analytics_topics(date_filter=date_filter)

        # Cache the result for 5 minutes
        cache_service.set("topics", cache_params, result, ttl_seconds=300)

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics topics: {str(e)}")

@router.get("/examples")
async def get_feedback_examples(
    topic_id: Optional[int] = Query(None, description="Topic ID filter"),
    sentiment: Optional[int] = Query(None, description="Sentiment filter (-1, 0, 1)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of examples (1-50)"),
    db: Session = Depends(get_db)
):
    """Get sample feedback comments with optional topic and sentiment filters"""
    try:
        # Create cache key parameters
        cache_params = {"topic_id": topic_id, "sentiment": sentiment, "limit": limit}

        # Try to get from cache first
        cached_result = cache_service.get("examples", cache_params)
        if cached_result:
            return cached_result

        repo = AnalyticsRepository(db)

        # Get feedback examples
        result = repo.get_feedback_examples(
            topic_id=topic_id,
            sentiment=sentiment,
            limit=limit
        )

        # Cache the result for 5 minutes
        cache_service.set("examples", cache_params, result, ttl_seconds=300)

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch feedback examples: {str(e)}")

@router.get("/dashboard/summary")
async def get_dashboard_summary(db: Session = Depends(get_db)):
    """Get dashboard summary statistics"""
    try:
        repo = AnalyticsRepository(db)

        # Get various stats for dashboard
        total_feedback = repo.execute_query(
            "SELECT COUNT(*) as count FROM feedback",
            fetch="scalar"
        )

        recent_trends = repo.get_sentiment_trends(group_by="day", date_filter=None)
        top_topics = repo.get_topic_distribution(min_feedback_count=5)

        return {
            "total_feedback": total_feedback,
            "recent_trends": recent_trends[-7:] if recent_trends else [],  # Last 7 days
            "top_topics": top_topics[:10] if top_topics else []  # Top 10 topics
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard summary: {str(e)}")
