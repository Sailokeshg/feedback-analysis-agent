from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..services.database import get_db
from ..repositories import AnalyticsRepository, DateFilter

router = APIRouter()

@router.get("/topics")
async def get_topic_distribution(
    min_feedback_count: int = Query(1, ge=1, description="Minimum feedback count per topic"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get topic distribution with sentiment analysis"""
    try:
        repo = AnalyticsRepository(db)

        # Create date filter if provided
        date_filter = DateFilter(
            start_date=start_date,
            end_date=end_date
        ) if start_date or end_date else None

        # Get topic distribution
        result = repo.get_topic_distribution(
            date_filter=date_filter,
            min_feedback_count=min_feedback_count
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch topic distribution: {str(e)}")

@router.get("/analytics/customers")
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

@router.get("/analytics/sources")
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

@router.get("/analytics/toxicity")
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
