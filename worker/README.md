# Worker - Background Processing

RQ-based worker for processing customer feedback in the background.

## Development

```bash
pip install -e .
python run_worker.py
```

## Tasks

- `process_feedback_batch` - Analyze sentiment and cluster topics for uploaded feedback

## Tech Stack

- RQ (Redis Queue)
- SQLAlchemy for database access
- Sentence Transformers for embeddings
- Chroma for vector storage
