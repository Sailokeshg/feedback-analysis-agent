"""
Router groups for the FastAPI application.
"""

from .ingest import router as ingest_router
from .analytics import router as analytics_router
from .chat import router as chat_router
from .admin import router as admin_router

__all__ = [
    "ingest_router",
    "analytics_router",
    "chat_router",
    "admin_router"
]
