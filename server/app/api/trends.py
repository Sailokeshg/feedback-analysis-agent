from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..services.database import get_db
from ..repositories import AnalyticsRepository, DateFilter

router = APIRouter()

@router.get("/trends/sentiment")
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

@router.get("/trends/volume")
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

@router.get("/trends/daily")
async def get_daily_aggregates(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(30, ge=1, le=365, description="Days per page (max 365)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get daily feedback aggregates"""
    try:
        from ..repositories import PaginationParams

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
