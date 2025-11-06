# Infrastructure - Docker Setup

Docker Compose configuration for local development and deployment.

## Services

- **postgres**: PostgreSQL database
- **redis**: Redis cache and queue
- **chroma**: Vector database for embeddings
- **server**: FastAPI backend
- **worker**: RQ background worker
- **client**: React dashboard

## Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```
