from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import feedback, topics, trends, query, upload

app = FastAPI(
    title="AI Customer Insights Agent API",
    description="API for processing and analyzing customer feedback",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(feedback.router, prefix="/api", tags=["feedback"])
app.include_router(topics.router, prefix="/api", tags=["topics"])
app.include_router(trends.router, prefix="/api", tags=["trends"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(upload.router, prefix="/api", tags=["upload"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
