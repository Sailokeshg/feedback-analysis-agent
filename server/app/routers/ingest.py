"""
Ingestion router for data intake operations.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from ..services.database import get_db
from ..repositories import FeedbackRepository
from ..config import settings

router = APIRouter()

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

@router.post("/feedback/batch")
async def create_feedback_batch(
    feedback_items: List[dict],
    db: Session = Depends(get_db)
):
    """Create multiple feedback items in batch"""
    try:
        repo = FeedbackRepository(db)
        results = []

        for item in feedback_items:
            feedback = repo.create_feedback(
                source=item.get("source", "api"),
                text=item["text"],
                customer_id=item.get("customer_id"),
                meta=item.get("meta", {})
            )
            results.append({
                "id": str(feedback.id),
                "source": feedback.source,
                "created_at": feedback.created_at.isoformat()
            })

        return {"created": results, "count": len(results)}

    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create feedback batch: {str(e)}")

@router.post("/upload/csv")
async def upload_csv_feedback(
    file: UploadFile = File(...),
    source: str = "csv_upload",
    db: Session = Depends(get_db)
):
    """Upload feedback from CSV file"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")

        content = await file.read()
        csv_text = content.decode('utf-8')

        # Simple CSV parsing (in production, use pandas or csv module)
        lines = csv_text.strip().split('\n')
        if not lines:
            raise HTTPException(status_code=400, detail="CSV file is empty")

        header = lines[0].split(',')
        if 'text' not in [h.strip().lower() for h in header]:
            raise HTTPException(status_code=400, detail="CSV must contain a 'text' column")

        repo = FeedbackRepository(db)
        results = []

        for line_num, line in enumerate(lines[1:], 2):  # Start from line 2
            if not line.strip():
                continue

            values = line.split(',')
            if len(values) != len(header):
                raise HTTPException(
                    status_code=400,
                    detail=f"Line {line_num}: Expected {len(header)} columns, got {len(values)}"
                )

            # Create dict from header and values
            item = {}
            for i, key in enumerate(header):
                item[key.strip()] = values[i].strip()

            if not item.get('text'):
                continue  # Skip empty text

            feedback = repo.create_feedback(
                source=source,
                text=item['text'],
                customer_id=item.get('customer_id'),
                meta={k: v for k, v in item.items() if k not in ['text', 'customer_id']}
            )

            results.append({
                "id": str(feedback.id),
                "line": line_num,
                "created_at": feedback.created_at.isoformat()
            })

        return {
            "message": f"Successfully uploaded {len(results)} feedback items",
            "results": results
        }

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")

@router.post("/upload/json")
async def upload_json_feedback(
    file: UploadFile = File(...),
    source: str = "json_upload",
    db: Session = Depends(get_db)
):
    """Upload feedback from JSON file"""
    try:
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="File must be a JSON file")

        content = await file.read()
        json_text = content.decode('utf-8')

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

        # Handle both single object and array
        if isinstance(data, dict):
            items = [data]
        elif isinstance(data, list):
            items = data
        else:
            raise HTTPException(status_code=400, detail="JSON must be an object or array of objects")

        repo = FeedbackRepository(db)
        results = []

        for item_num, item in enumerate(items, 1):
            if not isinstance(item, dict) or 'text' not in item:
                raise HTTPException(
                    status_code=400,
                    detail=f"Item {item_num}: Must be an object with a 'text' field"
                )

            feedback = repo.create_feedback(
                source=source,
                text=item['text'],
                customer_id=item.get('customer_id'),
                meta={k: v for k, v in item.items() if k not in ['text', 'customer_id']}
            )

            results.append({
                "id": str(feedback.id),
                "item": item_num,
                "created_at": feedback.created_at.isoformat()
            })

        return {
            "message": f"Successfully uploaded {len(results)} feedback items",
            "results": results
        }

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}")
