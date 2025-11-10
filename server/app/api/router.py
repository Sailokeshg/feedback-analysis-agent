"""
Combined API router that includes all API endpoints.
"""
from fastapi import APIRouter

from . import feedback, trends, topics, upload, query

# Create the main API router
router = APIRouter()

# Include all API sub-routers
router.include_router(feedback.router, tags=["feedback"])
router.include_router(trends.router, tags=["trends"])
router.include_router(topics.router, tags=["topics"])
router.include_router(upload.router, tags=["upload"])
router.include_router(query.router, tags=["query"])
