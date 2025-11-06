# AI Customer Insights Agent

A local-first MVP for analyzing customer feedback with sentiment analysis, topic clustering, and agentic Q&A capabilities.

## Architecture

- **Client**: React + TypeScript + Vite dashboard with Recharts visualizations
- **Server**: FastAPI backend with sentiment analysis and vector search
- **Worker**: RQ-based background processing for feedback analysis
- **Infrastructure**: Docker Compose with Postgres, Redis, and Chroma

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for development)
- Python 3.9+ (for development)

### Bootstrap
```bash
# Clone and bootstrap
make bootstrap

# Start all services
make docker-up

# Or run in development mode
make dev
```

### Development
```bash
# Setup development environment
make dev-setup

# Start development servers
make dev

# Run tests
make test

# Format code
make format
```

## Services

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:5432
- **Redis**: localhost:6379

## Features

- 📊 Sentiment analysis using VADER/Hugging Face models
- 🧠 Topic clustering with sentence-transformers
- 💬 Agentic Q&A for natural language queries
- 📈 Interactive dashboard with charts
- 🔄 Background processing with RQ workers
- 🐳 Local deployment with Docker

## Tech Stack

**Client:**
- React 18 + TypeScript
- Vite + Zustand + Recharts
- Axios for API calls

**Server:**
- FastAPI + Pydantic
- SQLAlchemy + PostgreSQL
- Redis + RQ workers

**AI/ML:**
- Sentence Transformers (embeddings)
- Chroma/FAISS (vector search)
- VADER/Hugging Face (sentiment)

**Infrastructure:**
- Docker Compose
- GitHub Actions CI/CD
- Pre-commit hooks

## Project Structure

```
├── client/          # React dashboard
├── server/          # FastAPI backend
├── worker/          # RQ background worker
├── infra/           # Docker configuration
├── scripts/         # Utility scripts
└── README.md
```

## Contributing

1. Install development dependencies: `make dev-setup`
2. Run pre-commit hooks: `pre-commit install`
3. Format code: `make format`
4. Run tests: `make test`

## License

MIT
