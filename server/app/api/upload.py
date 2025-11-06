import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..services.upload_service import UploadService

router = APIRouter()

@router.post("/upload")
async def upload_feedback_file(file: UploadFile = File(...)):
    """Upload a CSV file containing customer feedback"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")

        upload_service = UploadService()
        result = await upload_service.process_upload(file)

        return {
            "message": "File uploaded successfully",
            "processed_items": result["processed_count"],
            "status": "processing_started"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
