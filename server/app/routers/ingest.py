"""
Ingestion router for data intake operations.
"""

import csv
import io
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from ..services.database import get_db
from ..repositories import FeedbackRepository
from ..jobs import enqueue_feedback_ingestion
from ..config import settings

router = APIRouter()

class IngestResponse(BaseModel):
    """Response model for ingest operations."""
    batch_id: str
    processed_count: int
    created_count: int
    duplicate_count: int
    error_count: int
    skipped_non_english_count: int = 0
    job_id: Optional[str] = None

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

@router.post("/", response_model=IngestResponse)
async def ingest_feedback_data(
    file: UploadFile = File(...),
    source: str = Form("ingest_api", description="Source identifier for the feedback"),
    process_async: bool = Form(True, description="Process feedback asynchronously"),
    db: Session = Depends(get_db)
):
    """
    Ingest feedback data from CSV or JSONL file.

    Validates each row for required fields and stores in database with duplicate detection.
    Enqueues background processing job for NLP analysis.

    Supported formats:
    - CSV: text,created_at?,customer_id?,meta?
    - JSONL: {"text": "...", "created_at": "...", "customer_id": "...", "meta": {...}}
    """
    try:
        # Validate file format
        if not (file.filename.endswith('.csv') or file.filename.endswith('.jsonl') or file.filename.endswith('.json')):
            raise HTTPException(
                status_code=400,
                detail="File must be CSV (.csv) or JSONL (.jsonl/.json)"
            )

        # Read file content
        content = await file.read()
        file_content = content.decode('utf-8')

        # Parse data based on format
        feedback_items = []

        if file.filename.endswith('.csv'):
            feedback_items = _parse_csv_data(file_content)
        else:  # JSONL
            feedback_items = _parse_jsonl_data(file_content)

        if not feedback_items:
            raise HTTPException(status_code=400, detail="No valid feedback items found in file")

        # Generate batch ID
        batch_id = str(uuid.uuid4())

        # Process batch with duplicate detection
        repo = FeedbackRepository(db)
        batch_result = repo.create_feedback_batch(feedback_items, source)

        # Update source in meta for tracking
        for item in batch_result["created"] + batch_result["duplicates"]:
            # Mark items as part of this batch
            pass  # Could update meta with batch_id if needed

        # Enqueue background processing job if requested
        job_id = None
        if process_async and batch_result["created"]:
            feedback_ids = [item["id"] for item in batch_result["created"]]
            try:
                job_id = enqueue_feedback_ingestion(
                    feedback_ids=feedback_ids,
                    batch_id=batch_id,
                    source=source
                )
            except Exception as e:
                # Log error but don't fail the ingestion
                print(f"Failed to enqueue processing job: {e}")

        return IngestResponse(
            batch_id=batch_id,
            processed_count=batch_result["summary"]["total_processed"],
            created_count=batch_result["summary"]["created_count"],
            duplicate_count=batch_result["summary"]["duplicate_count"],
            error_count=batch_result["summary"]["error_count"],
            job_id=job_id
        )

    except HTTPException:
        raise
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process ingestion: {str(e)}")

def _parse_csv_data(csv_content: str) -> List[Dict[str, Any]]:
    """Parse CSV data into feedback items."""
    feedback_items = []

    # Use csv module for proper parsing
    reader = csv.DictReader(io.StringIO(csv_content))

    for row_num, row in enumerate(reader, 1):
        # Validate required text field
        text = row.get('text', '').strip()
        if not text:
            continue  # Skip empty rows

        item = {"text": text}

        # Optional fields
        if row.get('created_at', '').strip():
            item['created_at'] = row['created_at'].strip()

        if row.get('customer_id', '').strip():
            item['customer_id'] = row['customer_id'].strip()

        # Meta field - everything else goes into meta
        meta = {}
        for key, value in row.items():
            if key not in ['text', 'created_at', 'customer_id'] and value.strip():
                meta[key] = value.strip()

        if meta:
            item['meta'] = meta

        feedback_items.append(item)

    return feedback_items

def _parse_jsonl_data(jsonl_content: str) -> List[Dict[str, Any]]:
    """Parse JSONL data into feedback items."""
    feedback_items = []

    for line_num, line in enumerate(jsonl_content.strip().split('\n'), 1):
        line = line.strip()
        if not line:
            continue

        try:
            item = json.loads(line)

            # Validate it's a dict with text field
            if not isinstance(item, dict):
                continue

            text = item.get('text', '').strip()
            if not text:
                continue

            # Ensure required fields and clean up
            cleaned_item = {"text": text}

            if item.get('created_at'):
                cleaned_item['created_at'] = item['created_at']

            if item.get('customer_id'):
                cleaned_item['customer_id'] = item['customer_id']

            # Meta - everything except the main fields
            meta = {}
            for key, value in item.items():
                if key not in ['text', 'created_at', 'customer_id']:
                    meta[key] = value

            if meta:
                cleaned_item['meta'] = meta

            feedback_items.append(cleaned_item)

        except json.JSONDecodeError:
            # Skip malformed JSON lines
            continue

    return feedback_items

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

@router.post("/", response_model=IngestResponse)
async def ingest_feedback_data(
    file: UploadFile = File(...),
    source: str = Form("ingest_api", description="Source identifier for the feedback"),
    process_async: bool = Form(True, description="Process feedback asynchronously"),
    db: Session = Depends(get_db)
):
    """
    Ingest feedback data from CSV or JSONL file.

    Validates each row for required fields and stores in database with duplicate detection.
    Enqueues background processing job for NLP analysis.

    Supported formats:
    - CSV: text,created_at?,customer_id?,meta?
    - JSONL: {"text": "...", "created_at": "...", "customer_id": "...", "meta": {...}}
    """
    try:
        # Validate file format
        if not (file.filename.endswith('.csv') or file.filename.endswith('.jsonl') or file.filename.endswith('.json')):
            raise HTTPException(
                status_code=400,
                detail="File must be CSV (.csv) or JSONL (.jsonl/.json)"
            )

        # Read file content
        content = await file.read()
        file_content = content.decode('utf-8')

        # Parse data based on format
        feedback_items = []

        if file.filename.endswith('.csv'):
            feedback_items = _parse_csv_data(file_content)
        else:  # JSONL
            feedback_items = _parse_jsonl_data(file_content)

        if not feedback_items:
            raise HTTPException(status_code=400, detail="No valid feedback items found in file")

        # Generate batch ID
        batch_id = str(uuid.uuid4())

        # Process batch with duplicate detection
        repo = FeedbackRepository(db)
        batch_result = repo.create_feedback_batch(feedback_items, source)

        # Update source in meta for tracking
        for item in batch_result["created"] + batch_result["duplicates"]:
            # Mark items as part of this batch
            pass  # Could update meta with batch_id if needed

        # Enqueue background processing job if requested
        job_id = None
        if process_async and batch_result["created"]:
            feedback_ids = [item["id"] for item in batch_result["created"]]
            try:
                job_id = enqueue_feedback_ingestion(
                    feedback_ids=feedback_ids,
                    batch_id=batch_id,
                    source=source
                )
            except Exception as e:
                # Log error but don't fail the ingestion
                print(f"Failed to enqueue processing job: {e}")

        return IngestResponse(
            batch_id=batch_id,
            processed_count=batch_result["summary"]["total_processed"],
            created_count=batch_result["summary"]["created_count"],
            duplicate_count=batch_result["summary"]["duplicate_count"],
            error_count=batch_result["summary"]["error_count"],
            job_id=job_id
        )

    except HTTPException:
        raise
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process ingestion: {str(e)}")

def _parse_csv_data(csv_content: str) -> List[Dict[str, Any]]:
    """Parse CSV data into feedback items."""
    feedback_items = []

    # Use csv module for proper parsing
    reader = csv.DictReader(io.StringIO(csv_content))

    for row_num, row in enumerate(reader, 1):
        # Validate required text field
        text = row.get('text', '').strip()
        if not text:
            continue  # Skip empty rows

        item = {"text": text}

        # Optional fields
        if row.get('created_at', '').strip():
            item['created_at'] = row['created_at'].strip()

        if row.get('customer_id', '').strip():
            item['customer_id'] = row['customer_id'].strip()

        # Meta field - everything else goes into meta
        meta = {}
        for key, value in row.items():
            if key not in ['text', 'created_at', 'customer_id'] and value.strip():
                meta[key] = value.strip()

        if meta:
            item['meta'] = meta

        feedback_items.append(item)

    return feedback_items

def _parse_jsonl_data(jsonl_content: str) -> List[Dict[str, Any]]:
    """Parse JSONL data into feedback items."""
    feedback_items = []

    for line_num, line in enumerate(jsonl_content.strip().split('\n'), 1):
        line = line.strip()
        if not line:
            continue

        try:
            item = json.loads(line)

            # Validate it's a dict with text field
            if not isinstance(item, dict):
                continue

            text = item.get('text', '').strip()
            if not text:
                continue

            # Ensure required fields and clean up
            cleaned_item = {"text": text}

            if item.get('created_at'):
                cleaned_item['created_at'] = item['created_at']

            if item.get('customer_id'):
                cleaned_item['customer_id'] = item['customer_id']

            # Meta - everything except the main fields
            meta = {}
            for key, value in item.items():
                if key not in ['text', 'created_at', 'customer_id']:
                    meta[key] = value

            if meta:
                cleaned_item['meta'] = meta

            feedback_items.append(cleaned_item)

        except json.JSONDecodeError:
            # Skip malformed JSON lines
            continue

    return feedback_items
