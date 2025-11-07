"""
Admin router for administrative operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from fastapi import Request
from pydantic import BaseModel

from ..services.database import get_db
from ..services.auth_service import get_admin_user, get_viewer_user
from ..repositories import AnalyticsRepository, TopicRepository
from ..config import settings
from ..logging import get_logger

logger = get_logger("admin_api")

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

@router.get("/topics")
async def get_all_topics(db: Session = Depends(get_db)):
    """Get all topics for admin management."""
    try:
        from ..repositories import TopicRepository

        repo = TopicRepository(db)
        # This would need to be implemented in TopicRepository
        # For now, we'll use a simple query
        from ..models import Topic
        topics = db.query(Topic).order_by(Topic.label).all()

        return [
            {
                "id": topic.id,
                "label": topic.label,
                "keywords": topic.keywords,
                "updated_at": topic.updated_at.isoformat(),
            }
            for topic in topics
        ]

    except Exception as e:
        logger.error(f"Failed to get topics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get topics: {str(e)}")


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


class ReassignFeedbackRequest(BaseModel):
    """Request model for reassigning feedback to a different topic."""
    feedback_id: str  # UUID as string
    new_topic_id: int
    reason: Optional[str] = None


class ReassignFeedbackResponse(BaseModel):
    """Response model for feedback reassignment."""
    feedback_id: str
    old_topic_id: Optional[int]
    new_topic_id: int
    old_topic_label: Optional[str]
    new_topic_label: str
    reason: Optional[str]
    reassigned_at: str
    reassigned_by: str


@router.post("/login", response_model=LoginResponse)
async def admin_login(request: LoginRequest):
    """Authenticate admin user and return JWT token."""
    from ..services.auth_service import auth_service

    user = auth_service.authenticate_user(request.username, request.password)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create token with user info
    token_data = {
        "sub": user["username"],
        "role": user["role"]
    }
    access_token = auth_service.create_access_token(token_data)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.security.access_token_expire_minutes * 60
    )


@router.post("/viewer/login", response_model=LoginResponse)
async def viewer_login(request: LoginRequest):
    """Authenticate viewer user and return JWT token."""
    from ..services.auth_service import auth_service

    user = auth_service.authenticate_user(request.username, request.password)
    if not user or user["role"] != "viewer":
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create token with user info
    token_data = {
        "sub": user["username"],
        "role": user["role"]
    }
    access_token = auth_service.create_access_token(token_data)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.security.access_token_expire_minutes * 60
    )


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


@router.post("/reassign-feedback", response_model=ReassignFeedbackResponse)
async def reassign_feedback(
    request: ReassignFeedbackRequest,
    req: Request,
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Reassign a feedback comment to a different topic. Requires admin authentication."""
    try:
        from ..repositories import TopicRepository

        repo = TopicRepository(db)

        # Reassign feedback with audit logging
        result = repo.reassign_feedback_to_topic(
            feedback_id=request.feedback_id,
            new_topic_id=request.new_topic_id,
            changed_by=current_user.get("sub", "unknown"),
            reason=request.reason,
            ip_address=current_user.get("ip_address"),
            user_agent=current_user.get("user_agent")
        )

        # Refresh materialized view after reassignment
        try:
            from ..repositories import BaseRepository
            base_repo = BaseRepository(db)
            base_repo.execute_query("REFRESH MATERIALIZED VIEW daily_feedback_aggregates", fetch="none")
            logger.info("Refreshed materialized view after feedback reassignment")
        except Exception as e:
            logger.warning(f"Failed to refresh materialized view: {e}")

        return ReassignFeedbackResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to reassign feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reassign feedback: {str(e)}")


@router.get("/topics/{topic_id}/feedback")
async def get_topic_feedback(
    topic_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: Dict[str, Any] = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get feedback comments assigned to a specific topic. Requires admin authentication."""
    try:
        from ..repositories import AnalyticsRepository

        repo = AnalyticsRepository(db)

        # Get feedback examples for this topic
        examples = repo.get_feedback_examples(
            topic_id=topic_id,
            limit=page_size * page  # Get enough for pagination
        )

        # Manual pagination (since the repo method doesn't support offset)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_examples = examples[start_idx:end_idx] if examples else []

        # Get total count
        total_count = len(examples) if examples else 0
        total_pages = (total_count + page_size - 1) // page_size

        return {
            "topic_id": topic_id,
            "feedback": paginated_examples,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages
            }
        }

    except Exception as e:
        logger.error(f"Failed to get topic feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get topic feedback: {str(e)}")


# Viewer endpoints (accessible by both admin and viewer roles)
@router.get("/viewer/stats")
async def get_viewer_stats(db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_viewer_user)):
    """Get basic system statistics for viewers."""
    try:
        repo = AnalyticsRepository(db)

        # Get basic feedback stats
        total_feedback = repo.execute_query(
            "SELECT COUNT(*) FROM feedback",
            fetch="scalar"
        )

        # Get feedback from last 30 days
        recent_feedback = repo.execute_query(
            "SELECT COUNT(*) FROM feedback WHERE created_at >= NOW() - INTERVAL '30 days'",
            fetch="scalar"
        )

        return {
            "total_feedback": total_feedback,
            "recent_feedback_30d": recent_feedback,
            "user_role": current_user.get("role"),
            "username": current_user.get("sub")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch viewer stats: {str(e)}")


@router.get("/viewer/dashboard")
async def get_viewer_dashboard(db: Session = Depends(get_db), current_user: Dict[str, Any] = Depends(get_viewer_user)):
    """Get dashboard data for viewers."""
    try:
        repo = AnalyticsRepository(db)

        # Get basic topic distribution
        topics = repo.get_topic_distribution(limit=10)

        # Get recent sentiment trends
        sentiment_trends = repo.get_sentiment_trends(group_by="day", limit=7)

        return {
            "topics": topics,
            "sentiment_trends": sentiment_trends,
            "user_role": current_user.get("role"),
            "last_updated": "2024-11-07T12:00:00Z"  # Mock timestamp
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {str(e)}")


@router.get("/viewer/profile")
async def get_viewer_profile(current_user: Dict[str, Any] = Depends(get_viewer_user)):
    """Get current user profile information."""
    return {
        "username": current_user.get("sub"),
        "role": current_user.get("role"),
        "permissions": ["read:stats", "read:dashboard"] if current_user.get("role") == "viewer" else ["read:stats", "read:dashboard", "write:topics", "admin:system"],
        "login_time": current_user.get("iat"),
        "expires_at": current_user.get("exp")
    }
