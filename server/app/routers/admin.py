"""
Admin router for administrative operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..services.database import get_db
from ..repositories import AnalyticsRepository
from ..config import settings

router = APIRouter()

@router.get("/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """Get comprehensive system statistics"""
    try:
        repo = AnalyticsRepository(db)

        # Get various system stats
        total_feedback = repo.execute_query(
            "SELECT COUNT(*) FROM feedback",
            fetch="scalar"
        )

        total_annotations = repo.execute_query(
            "SELECT COUNT(*) FROM nlp_annotation",
            fetch="scalar"
        )

        total_topics = repo.execute_query(
            "SELECT COUNT(*) FROM topic",
            fetch="scalar"
        )

        # Get database size (approximate)
        db_size = repo.execute_query(
            "SELECT pg_size_pretty(pg_database_size(current_database())) as size",
            fetch="scalar"
        )

        # Get recent activity
        recent_feedback = repo.execute_query(
            "SELECT COUNT(*) FROM feedback WHERE created_at >= NOW() - INTERVAL '24 hours'",
            fetch="scalar"
        )

        return {
            "database": {
                "size": db_size,
                "connection_string": settings.database.url.replace(
                    settings.database.url.split('@')[0].split(':')[1], "***"
                )  # Hide password
            },
            "feedback": {
                "total": total_feedback,
                "recent_24h": recent_feedback
            },
            "annotations": {
                "total": total_annotations
            },
            "topics": {
                "total": total_topics
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch system stats: {str(e)}")

@router.post("/maintenance/refresh-materialized-view")
async def refresh_materialized_view(db: Session = Depends(get_db)):
    """Refresh the daily feedback aggregates materialized view"""
    try:
        from ..repositories import BaseRepository
        repo = BaseRepository(db)

        # Refresh the materialized view
        repo.execute_query("REFRESH MATERIALIZED VIEW daily_feedback_aggregates", fetch="none")

        return {
            "message": "Materialized view refreshed successfully",
            "view_name": "daily_feedback_aggregates"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh materialized view: {str(e)}")

@router.get("/health/database")
async def check_database_health(db: Session = Depends(get_db)):
    """Check database connectivity and basic functionality"""
    try:
        # Test basic connectivity
        result = db.execute("SELECT 1 as test").fetchone()

        # Test table access
        feedback_count = db.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]

        return {
            "status": "healthy",
            "database_connection": "ok",
            "table_access": "ok",
            "feedback_count": feedback_count
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database_connection": "failed",
            "error": str(e)
        }

@router.get("/config")
async def get_config_info():
    """Get sanitized configuration information"""
    return {
        "api": {
            "title": settings.api.title,
            "version": settings.api.version,
            "debug": settings.api.debug
        },
        "database": {
            "pool_size": settings.database.pool_size,
            "max_overflow": settings.database.max_overflow
        },
        "rate_limit": {
            "enabled": settings.rate_limit.enabled,
            "requests_per_minute": settings.rate_limit.requests_per_minute
        },
        "cors": {
            "allow_origins": settings.cors.allow_origins,
            "allow_credentials": settings.cors.allow_credentials
        }
    }

@router.post("/cleanup/old-data")
async def cleanup_old_data(
    days_to_keep: int = 365,
    dry_run: bool = True,
    db: Session = Depends(get_db)
):
    """Clean up old feedback data (with dry run option)"""
    try:
        from ..repositories import BaseRepository
        repo = BaseRepository(db)

        # Count records that would be deleted
        cutoff_date = f"NOW() - INTERVAL '{days_to_keep} days'"

        count_query = f"""
        SELECT COUNT(*) FROM feedback
        WHERE created_at < {cutoff_date}
        """

        records_to_delete = repo.execute_query(count_query, fetch="scalar")

        if dry_run:
            return {
                "dry_run": True,
                "records_to_delete": records_to_delete,
                "cutoff_date": f"{days_to_keep} days ago",
                "message": f"Would delete {records_to_delete} feedback records older than {days_to_keep} days"
            }

        # Perform actual deletion
        delete_query = f"""
        DELETE FROM feedback
        WHERE created_at < {cutoff_date}
        """

        repo.execute_query(delete_query, fetch="none")

        # Refresh materialized view after cleanup
        repo.execute_query("REFRESH MATERIALIZED VIEW daily_feedback_aggregates", fetch="none")

        return {
            "dry_run": False,
            "records_deleted": records_to_delete,
            "cutoff_date": f"{days_to_keep} days ago",
            "message": f"Successfully deleted {records_to_delete} old feedback records"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup old data: {str(e)}")

@router.get("/logs/recent")
async def get_recent_logs(lines: int = 50):
    """Get recent application logs (placeholder)"""
    # In a real implementation, this would read from log files
    return {
        "logs": [
            "Application started",
            "Database connected",
            "Rate limiting enabled"
        ],
        "lines_requested": lines,
        "note": "Log reading not implemented - this is a placeholder"
    }

@router.post("/cache/clear")
async def clear_application_cache():
    """Clear application caches (placeholder)"""
    # In a real implementation, this would clear Redis caches, etc.
    return {
        "message": "Cache clearing not implemented - this is a placeholder",
        "cleared": []
    }
