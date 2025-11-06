# Server - FastAPI Backend

FastAPI backend providing REST API for customer feedback analysis.

## Development

```bash
pip install -e .
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /api/feedback` - List feedback items
- `GET /api/topics` - Get topic clusters
- `GET /api/trends` - Get sentiment trends
- `POST /api/query` - Natural language queries
- `POST /api/upload` - Upload feedback CSV

## Tech Stack

- FastAPI + Uvicorn
- SQLAlchemy + PostgreSQL
- Pydantic for validation
- Redis + RQ for background jobs

## Structure

```
app/
├── api/           # API route handlers
├── models/        # Database models
├── services/      # Business logic
└── utils/         # Utilities
```
