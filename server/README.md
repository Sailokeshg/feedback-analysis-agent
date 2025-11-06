# AI Customer Insights Server

FastAPI backend for AI Customer Insights Agent with sentiment analysis and vector search.

## Database Setup

### Prerequisites
- PostgreSQL 15+
- Python 3.9+

### Initial Setup

1. **Install dependencies:**
   ```bash
   pip install -e .[dev]
   ```

2. **Set up database:**
   ```bash
   # Create database
   createdb feedback_db

   # Or using Docker
   docker run -d --name postgres \
     -e POSTGRES_DB=feedback_db \
     -e POSTGRES_USER=user \
     -e POSTGRES_PASSWORD=password \
     -p 5432:5432 postgres:15
   ```

3. **Run migrations:**
   ```bash
   # Initialize database schema
   alembic upgrade head

   # Or run specific migration
   alembic upgrade 001
   ```

4. **Seed with fake data:**
   ```bash
   python scripts/seed_database.py
   ```

### Database Schema

#### Tables

- **`feedback`**: Customer feedback entries
  - `id` (UUID): Primary key
  - `source` (text): Origin of feedback (website, mobile_app, etc.)
  - `created_at` (timestamptz): Creation timestamp
  - `customer_id` (text, nullable): Customer identifier
  - `text` (text): Feedback content
  - `meta` (jsonb): Additional metadata

- **`nlp_annotation`**: NLP analysis results for feedback
  - `id` (serial): Primary key
  - `feedback_id` (UUID, FK): Reference to feedback
  - `sentiment` (smallint): -1 (negative), 0 (neutral), 1 (positive)
  - `sentiment_score` (float): Confidence score for sentiment
  - `topic_id` (int, FK, nullable): Reference to topic
  - `toxicity_score` (float, nullable): Toxicity detection score
  - `embedding` (vector/bytea): Text embedding for similarity search

- **`topic`**: Topic clusters for feedback categorization
  - `id` (serial): Primary key
  - `label` (text): Topic name
  - `keywords` (text[]): Associated keywords
  - `updated_at` (timestamptz): Last update timestamp

#### Materialized View

- **`daily_feedback_aggregates`**: Daily statistics
  - `date`: Aggregation date
  - `total_feedback`: Total feedback count
  - `positive_count`: Positive sentiment count
  - `neutral_count`: Neutral sentiment count
  - `negative_count`: Negative sentiment count
  - `avg_sentiment_score`: Average sentiment confidence
  - `avg_toxicity_score`: Average toxicity score
  - `unique_customers`: Distinct customer count
  - `unique_topics`: Distinct topic count

### Migration Commands

```bash
# Show current migration status
alembic current

# Show migration history
alembic history

# Create new migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

### Notes

- **pgvector**: If pgvector extension is not available, modify the migration to use `bytea` instead of `vector(384)` for the embedding column.
- **Materialized View**: Refresh the view after bulk data operations:
  ```sql
  REFRESH MATERIALIZED VIEW daily_feedback_aggregates;
  ```

## Development

### Running the Server

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json