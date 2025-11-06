from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from ..models.feedback import FeedbackItem
from ..services.database import get_db

router = APIRouter()

@router.get("/trends")
async def get_sentiment_trends(db: Session = Depends(get_db)):
    """Get sentiment trends over time"""
    try:
        # Group by date and count sentiments
        result = db.query(
            cast(FeedbackItem.created_at, Date).label('date'),
            func.sum(func.case((FeedbackItem.sentiment == 'positive', 1), else_=0)).label('positive_count'),
            func.sum(func.case((FeedbackItem.sentiment == 'negative', 1), else_=0)).label('negative_count'),
            func.sum(func.case((FeedbackItem.sentiment == 'neutral', 1), else_=0)).label('neutral_count'),
        ).group_by(cast(FeedbackItem.created_at, Date)).order_by(cast(FeedbackItem.created_at, Date)).all()

        return [
            {
                "date": str(date),
                "positive": positive_count or 0,
                "negative": negative_count or 0,
                "neutral": neutral_count or 0,
            }
            for date, positive_count, negative_count, neutral_count in result
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trends: {str(e)}")
