from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .middleware import RateLimitMiddleware
from .routers import ingest_router, analytics_router, chat_router, admin_router

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

# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy"}

@app.get("/healthz")
async def healthz_check():
    """Kubernetes-style health check returning 'ok'"""
    return "ok"
