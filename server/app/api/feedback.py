from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models.feedback import FeedbackItem
from ..services.database import get_db

router = APIRouter()

@router.get("/feedback", response_model=List[dict])
async def get_feedback(limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    """Get paginated feedback items"""
    try:
        feedback = db.query(FeedbackItem).offset(offset).limit(limit).all()
        return [
            {
                "id": str(item.id),
                "text": item.text,
                "sentiment": item.sentiment,
                "sentiment_score": item.sentiment_score,
                "topic_cluster": item.topic_cluster,
                "created_at": item.created_at.isoformat(),
                "source": item.source,
            }
            for item in feedback
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch feedback: {str(e)}")

@router.get("/feedback/{feedback_id}")
async def get_feedback_item(feedback_id: str, db: Session = Depends(get_db)):
    """Get a specific feedback item"""
    try:
        feedback = db.query(FeedbackItem).filter(FeedbackItem.id == feedback_id).first()
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback item not found")

        return {
            "id": str(feedback.id),
            "text": feedback.text,
            "sentiment": feedback.sentiment,
            "sentiment_score": feedback.sentiment_score,
            "topic_cluster": feedback.topic_cluster,
            "created_at": feedback.created_at.isoformat(),
            "source": feedback.source,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch feedback item: {str(e)}")
