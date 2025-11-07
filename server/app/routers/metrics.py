"""
Metrics endpoint for Prometheus monitoring (development only).
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse

from ..metrics import get_metrics, is_development_mode
from ..logging import log

router = APIRouter()


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.

    Only available in development mode for security reasons.
    In production, metrics should be exposed through a separate service.
    """
    if not is_development_mode():
        log.warning("Metrics endpoint accessed in non-development mode")
        raise HTTPException(
            status_code=404,
            detail="Metrics endpoint not available"
        )

    try:
        metrics_data = get_metrics()
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        log.error("Failed to serve metrics", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail="Failed to generate metrics"
        )
