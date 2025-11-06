"""
Admin router for administrative operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from fastapi import Request
from pydantic import BaseModel

from ..services.database import get_db
from ..services.auth_service import get_admin_user
from ..repositories import AnalyticsRepository, TopicRepository
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


# Request/Response models for authentication
class LoginRequest(BaseModel):
    """Request model for admin login."""
    username: str
    password: str


class LoginResponse(BaseModel):
    """Response model for admin login."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# Request/Response models for topic operations
class RelabelTopicRequest(BaseModel):
    """Request model for relabeling a topic."""
    topic_id: int
    new_label: str
    new_keywords: List[str]


class RelabelTopicResponse(BaseModel):
    """Response model for topic relabeling."""
    topic_id: int
    old_label: str
    new_label: str
    old_keywords: List[str]
    new_keywords: List[str]
    updated_at: str
    changed_by: str


class TopicAuditLogResponse(BaseModel):
    """Response model for topic audit logs."""
    id: int
    topic_id: int
    topic_label: str
    action: str
    old_label: Optional[str]
    new_label: Optional[str]
    old_keywords: Optional[List[str]]
    new_keywords: Optional[List[str]]
    changed_by: str
    changed_at: str
    ip_address: Optional[str]
    user_agent: Optional[str]


@router.post("/login", response_model=LoginResponse)
async def admin_login(request: LoginRequest):
    """Authenticate admin user and return JWT token."""
    # Simple authentication for demo purposes
    # In production, you'd validate against a user database with proper password hashing
    if request.username == "admin" and request.password == "admin123":
        from ..services.auth_service import auth_service

        # Create token with user info
        token_data = {
            "sub": request.username,
            "is_admin": True,
            "role": "admin"
        }
        access_token = auth_service.create_access_token(token_data)

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.security.access_token_expire_minutes * 60
        )
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/relabel-topic", response_model=RelabelTopicResponse)
async def relabel_topic(
    request: RelabelTopicRequest,
    req: Request,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Relabel a topic with new label and keywords. Requires admin authentication."""
    try:
        repo = TopicRepository(db)

        # Get current topic for response
        current_topic = repo.get_topic_by_id(request.topic_id)
        if not current_topic:
            raise HTTPException(status_code=404, detail=f"Topic with ID {request.topic_id} not found")

        old_label = current_topic.label
        old_keywords = current_topic.keywords.copy() if current_topic.keywords else []

        # Update topic with audit logging
        updated_topic = repo.update_topic_label(
            topic_id=request.topic_id,
            new_label=request.new_label,
            new_keywords=request.new_keywords,
            changed_by=current_user.get("sub", "unknown"),
            ip_address=current_user.get("ip_address"),
            user_agent=current_user.get("user_agent")
        )

        return RelabelTopicResponse(
            topic_id=updated_topic.id,
            old_label=old_label,
            new_label=updated_topic.label,
            old_keywords=old_keywords,
            new_keywords=updated_topic.keywords,
            updated_at=updated_topic.updated_at.isoformat(),
            changed_by=current_user.get("sub", "unknown")
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to relabel topic: {str(e)}")


@router.get("/topic-audit/{topic_id}")
async def get_topic_audit_history(
    topic_id: int,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get audit history for a specific topic. Requires admin authentication."""
    try:
        repo = TopicRepository(db)
        audit_history = repo.get_topic_audit_history(topic_id)

        return {
            "topic_id": topic_id,
            "audit_logs": audit_history
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit history: {str(e)}")


@router.get("/topic-audit", response_model=List[TopicAuditLogResponse])
async def get_recent_topic_audit_logs(
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get recent topic audit logs across all topics. Requires admin authentication."""
    try:
        repo = TopicRepository(db)
        audit_logs = repo.get_recent_audit_logs(limit)

        return audit_logs

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit logs: {str(e)}")
