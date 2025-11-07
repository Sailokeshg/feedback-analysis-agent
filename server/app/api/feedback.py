from typing import List, Optional
from uuid import UUID
import time
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..services.database import get_db
from ..repositories import FeedbackRepository, PaginationParams, DateFilter
from ..logging import get_logger, request_id
from ..metrics import (
    increment_http_requests,
    observe_http_request_duration,
    increment_feedback_processed,
)

router = APIRouter()
log = get_logger("feedback_api")

@router.get("/feedback", response_model=dict)
async def get_feedback(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=1000, description="Items per page"),
    source: Optional[str] = Query(None, description="Filter by source"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get paginated feedback items with filtering"""
    start_time = time.time()
    request_id_val = request_id.get() or "unknown"

    log.info(
        "Fetching feedback list",
        extra={
            "request_id": request_id_val,
            "page": page,
            "page_size": page_size,
            "source_filter": source,
            "customer_id_filter": customer_id,
            "date_filter": {
                "start_date": start_date,
                "end_date": end_date
            } if start_date or end_date else None,
        }
    )

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

        duration = time.time() - start_time
        observe_http_request_duration("GET", "/api/feedback", duration)

        log.info(
            "Feedback list retrieved successfully",
            extra={
                "request_id": request_id_val,
                "total_items": result.get("total", 0),
                "returned_items": len(result.get("items", [])),
                "duration_ms": round(duration * 1000, 2),
            }
        )

        return result

    except ValueError as e:
        duration = time.time() - start_time
        increment_http_requests("GET", "/api/feedback", 400)

        log.warning(
            "Invalid parameters for feedback list",
            extra={
                "request_id": request_id_val,
                "error": str(e),
                "duration_ms": round(duration * 1000, 2),
            }
        )
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        duration = time.time() - start_time
        increment_http_requests("GET", "/api/feedback", 500)

        log.error(
            "Failed to fetch feedback list",
            extra={
                "request_id": request_id_val,
                "error": str(e),
                "error_type": type(e).__name__,
                "duration_ms": round(duration * 1000, 2),
            }
        )
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
    request: Request,
    source: str,
    text: str,
    customer_id: Optional[str] = None,
    meta: Optional[dict] = None,
    db: Session = Depends(get_db)
):
    """Create a new feedback item"""
    start_time = time.time()
    request_id_val = request_id.get() or "unknown"

    log.info(
        "Creating new feedback item",
        extra={
            "request_id": request_id_val,
            "source": source,
            "text_length": len(text),
            "customer_id": customer_id,
            "has_meta": meta is not None,
        }
    )

    try:
        repo = FeedbackRepository(db)

        feedback = repo.create_feedback(
            source=source,
            text=text,
            customer_id=customer_id,
            meta=meta or {}
        )

        duration = time.time() - start_time
        increment_http_requests("POST", "/api/feedback", 201)
        observe_http_request_duration("POST", "/api/feedback", duration)
        increment_feedback_processed(source, "created")

        log.info(
            "Feedback item created successfully",
            extra={
                "request_id": request_id_val,
                "feedback_id": str(feedback.id),
                "source": source,
                "duration_ms": round(duration * 1000, 2),
            }
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
        duration = time.time() - start_time
        increment_http_requests("POST", "/api/feedback", 500)

        log.error(
            "Failed to create feedback item",
            extra={
                "request_id": request_id_val,
                "source": source,
                "error": str(e),
                "error_type": type(e).__name__,
                "duration_ms": round(duration * 1000, 2),
            }
        )
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
