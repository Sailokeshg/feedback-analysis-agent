from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .middleware import RateLimitMiddleware
from .routers import ingest_router, analytics_router, chat_router, admin_router
from .routers.metrics import router as metrics_router
from .logging import setup_logging, LoggingSettings
from .middleware.request_timing import RequestTimingMiddleware
from .metrics import set_service_health

# Setup logging
logging_settings = LoggingSettings()
setup_logging(logging_settings)

# Create FastAPI app with settings
app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version,
    docs_url=settings.api.docs_url,
    redoc_url=settings.api.redoc_url,
    openapi_url=settings.api.openapi_url,
    debug=settings.api.debug,
)

# Request timing middleware (must be first)
app.add_middleware(RequestTimingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allow_origins,
    allow_credentials=settings.cors.allow_credentials,
    allow_methods=settings.cors.allow_methods,
    allow_headers=settings.cors.allow_headers,
    max_age=settings.cors.max_age,
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(
    ingest_router,
    prefix="/ingest",
    tags=["ingest"]
)
app.include_router(
    analytics_router,
    prefix="/analytics",
    tags=["analytics"]
)
app.include_router(
    chat_router,
    prefix="/chat",
    tags=["chat"]
)
app.include_router(
    admin_router,
    prefix="/admin",
    tags=["admin"]
)

# Metrics router (development only)
app.include_router(metrics_router)

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    # Update service health metric
    set_service_health("api", True)
    return {"status": "healthy"}

@app.get("/healthz")
async def healthz_check():
    """Kubernetes-style health check returning 'ok'"""
    return "ok"
