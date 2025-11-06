from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.feedback import FeedbackItem
from ..services.database import get_db

router = APIRouter()

@router.get("/topics")
async def get_topic_clusters(db: Session = Depends(get_db)):
    """Get topic clusters with sentiment distribution"""
    try:
        # Group by topic_cluster and count sentiments
        result = db.query(
            FeedbackItem.topic_cluster,
            func.count(FeedbackItem.id).label('total_count'),
            func.sum(func.case((FeedbackItem.sentiment == 'positive', 1), else_=0)).label('positive_count'),
            func.sum(func.case((FeedbackItem.sentiment == 'negative', 1), else_=0)).label('negative_count'),
            func.sum(func.case((FeedbackItem.sentiment == 'neutral', 1), else_=0)).label('neutral_count'),
        ).group_by(FeedbackItem.topic_cluster).all()

        return [
            {
                "id": topic_cluster,
                "name": topic_cluster,
                "count": total_count,
                "sentiment_distribution": {
                    "positive": positive_count or 0,
                    "negative": negative_count or 0,
                    "neutral": neutral_count or 0,
                }
            }
            for topic_cluster, total_count, positive_count, negative_count, neutral_count in result
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch topics: {str(e)}")
