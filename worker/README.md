# Feedback Analysis Worker

Redis RQ worker for processing feedback analysis jobs across multiple queues.

## Queues

The worker processes jobs from four specialized queues:

- **ingest**: Initial data validation and preprocessing
- **annotate**: NLP analysis, sentiment detection, toxicity scoring
- **cluster**: Topic modeling and feedback grouping
- **reports**: Analytics generation and materialized view updates

## Usage

### Start Worker (All Queues)

```bash
python worker.py
```

### Start Worker (Specific Queues)

```bash
# Process only ingest and annotate queues
python worker.py --queues ingest annotate

# Process only reports queue
python worker.py --queues reports
```

### Check Queue Statistics

```bash
python worker.py --stats
```

### Verbose Logging

```bash
python worker.py --verbose
```

## Job Flow

1. **Ingest Queue**: Validates and preprocesses newly uploaded feedback
2. **Annotate Queue**: Performs sentiment analysis and toxicity detection
3. **Cluster Queue**: Groups similar feedback into topics
4. **Reports Queue**: Generates analytics and updates cache

Jobs automatically flow from one queue to the next, ensuring complete processing pipelines.

## Configuration

The worker uses the same configuration as the main application (`server/app/config.py`):

- Redis URL from `EXTERNAL_REDIS_URL` environment variable
- Falls back to `redis://localhost:6379`

## Monitoring

The worker logs all job processing activity. Use `--stats` to monitor queue depths and job status.

## Development

For local development, ensure Redis is running:

```bash
# Start Redis (if using Docker)
docker run -d -p 6379:6379 redis:alpine

# Or install locally
brew install redis
redis-server
```

Then start the worker:

```bash
cd worker
python worker.py --verbose
```