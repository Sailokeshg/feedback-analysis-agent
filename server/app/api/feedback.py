from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..services.database import get_db
from ..repositories import FeedbackRepository, PaginationParams, DateFilter

router = APIRouter()

@router.get("/feedback", response_model=dict)
async def get_feedback(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    source: Optional[str] = Query(None, description="Filter by source"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get paginated feedback items with filtering"""
    try:
        repo = FeedbackRepository(db)

        # Create pagination and filter objects
        pagination = PaginationParams(page=page, page_size=page_size)
        date_filter = DateFilter(
            start_date=start_date,
            end_date=end_date
        ) if start_date or end_date else None

        # Get feedback list
        result = repo.get_feedback_list(
            pagination=pagination,
            date_filter=date_filter,
            source_filter=source,
            customer_id_filter=customer_id
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch feedback: {str(e)}")

@router.get("/feedback/{feedback_id}")
async def get_feedback_item(feedback_id: str, db: Session = Depends(get_db)):
    """Get a specific feedback item with annotations"""
    try:
        repo = FeedbackRepository(db)

        # Validate UUID format
        try:
            feedback_uuid = UUID(feedback_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid feedback ID format")

        # Get feedback with annotations
        feedback = repo.get_feedback_with_annotations(feedback_uuid)

        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback item not found")

        return feedback

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch feedback item: {str(e)}")

@router.post("/feedback")
async def create_feedback(
    source: str,
    text: str,
    customer_id: Optional[str] = None,
    meta: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """Create a new feedback item"""
    try:
        repo = FeedbackRepository(db)

        feedback = repo.create_feedback(
            source=source,
            text=text,
            customer_id=customer_id,
            meta=meta or {}
        )

        return {
            "id": str(feedback.id),
            "source": feedback.source,
            "text": feedback.text,
            "customer_id": feedback.customer_id,
            "created_at": feedback.created_at.isoformat(),
            "meta": feedback.meta
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create feedback: {str(e)}")

@router.get("/feedback/search")
async def search_feedback(
    q: str = Query(..., description="Search query"),
    sentiment: Optional[int] = Query(None, description="Filter by sentiment (-1, 0, 1)"),
    topic_id: Optional[int] = Query(None, description="Filter by topic ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Search feedback with advanced filters"""
    try:
        repo = FeedbackRepository(db)

        # Create pagination and filter objects
        pagination = PaginationParams(page=page, page_size=page_size)
        date_filter = DateFilter(
            start_date=start_date,
            end_date=end_date
        ) if start_date or end_date else None

        # Perform search
        result = repo.search_feedback(
            search_text=q,
            sentiment_filter=sentiment,
            topic_id_filter=topic_id,
            pagination=pagination,
            date_filter=date_filter
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search feedback: {str(e)}")
