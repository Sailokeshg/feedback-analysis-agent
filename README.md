# AI Customer Insights Agent

[![Server CI](https://github.com/your-org/feedback-analysis-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/feedback-analysis-agent/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/your-org/feedback-analysis-agent/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/feedback-analysis-agent)

A local-first MVP for analyzing customer feedback with sentiment analysis, topic clustering, and agentic Q&A capabilities. Built with structured logging, comprehensive metrics, and production-ready architecture.

## 🚀 Quick Start (≤10 minutes)

### Prerequisites
- Docker & Docker Compose (latest versions)
- Node.js 18+ (for development)
- Python 3.9+ (for development)

### Step 1: Clone and Bootstrap
```bash
git clone https://github.com/your-org/feedback-analysis-agent.git
cd feedback-analysis-agent

# Bootstrap everything (installs dependencies, sets up services)
make bootstrap
```

### Step 2: Start Services
```bash
# Start all services with Docker
make docker-up

# Wait for services to be ready (~30 seconds)
```

### Step 3: Access the Application
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Step 4: Add Sample Data
```bash
# Upload sample feedback via API
curl -X POST http://localhost:8000/api/upload/csv \
  -F "file=@server/test_data/sample_feedback.csv"
```

### Step 5: Explore Features
1. View sentiment trends in the dashboard
2. Ask questions via the chat interface
3. Check metrics at http://localhost:8000/metrics (dev mode)

## 🏗️ Architecture

```mermaid
graph TB
    A[React Dashboard<br/>localhost:3000] --> B[FastAPI Server<br/>localhost:8000]
    B --> C[PostgreSQL<br/>localhost:5432]
    B --> D[Redis Queue<br/>localhost:6379]
    B --> E[Chroma Vector DB<br/>localhost:8000]

    D --> F[RQ Worker]
    F --> C
    F --> E

    B --> G[Metrics Endpoint<br/>/metrics]
    B --> H[Health Checks<br/>/health]

    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style F fill:#e8f5e8
    style G fill:#fff3e0
    style H fill:#ffebee
```

**Components:**
- **Client**: React dashboard with real-time charts and chat interface
- **Server**: FastAPI backend with sentiment analysis and vector search
- **Worker**: RQ-based background processing for heavy ML tasks
- **Infrastructure**: Docker Compose with PostgreSQL, Redis, and Chroma

## 📋 Environment Variables

### Database Configuration
```bash
# PostgreSQL settings
POSTGRES_DB=feedback_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
DATABASE_URL=postgresql://user:password@localhost:5432/feedback_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

### External Services
```bash
# Redis for queues and caching
REDIS_URL=redis://localhost:6379

# Chroma vector database
EXTERNAL_CHROMA_URL=http://localhost:8000
```

### API Configuration
```bash
# Server settings
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# CORS settings
CORS_ALLOW_ORIGINS=["http://localhost:3000"]
CORS_ALLOW_CREDENTIALS=true
```

### Logging & Monitoring
```bash
# Logging configuration
LOG_LEVEL=INFO
LOG_JSON_LOGS=true
LOG_FILE=logs/app.log
LOG_ROTATION=10 MB
LOG_RETENTION=1 week

# Environment detection
ENVIRONMENT=development  # or production
```

### ML & AI Settings
```bash
# Sentiment analysis
USE_HF_SENTIMENT=false  # true for Hugging Face, false for VADER

# Processing settings
BATCH_SIZE=32
MAX_SEQUENCE_LENGTH=256
```

## 🎯 Make Targets

### Development
```bash
make help              # Show all available commands
make bootstrap         # Initial project setup
make dev-setup         # Install development dependencies
make dev               # Start all development servers
```

### Testing
```bash
make test              # Run all tests with coverage
make test-server       # Test server only
make test-worker       # Test worker only
make test-client       # Test client only
make test-logging      # Test logging/metrics integration
```

### Code Quality
```bash
make lint              # Run all linters
make format            # Format code (Python + TypeScript)
make demo-logging      # Demonstrate logging/metrics
```

### Docker & Infrastructure
```bash
make docker-up         # Start all services
make docker-down       # Stop all services
make build             # Build Docker images
make clean             # Clean up artifacts
```

## 🔧 Development Workflow

### Local Development
```bash
# Setup development environment
make dev-setup

# Start services in background
make docker-up

# Start development servers
make dev

# The application will be available at:
# - Frontend: http://localhost:3000
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Metrics: http://localhost:8000/metrics (dev only)
```

### Running Tests
```bash
# Run all tests
make test

# Run specific test suites
make test-server       # Server tests with 80% coverage
make test-worker       # Worker tests
make test-client       # Client tests

# Run logging demonstration
make demo-logging
```

### Code Formatting
```bash
# Format all code
make format

# Lint all code
make lint
```

## 🐛 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check if Docker is running
docker --version
docker-compose --version

# Restart Docker services
make docker-down
make docker-up

# Check service logs
docker-compose -f infra/docker-compose.yml logs
```

#### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose -f infra/docker-compose.yml ps postgres

# Reset database
make clean
make docker-up

# Check database logs
docker-compose -f infra/docker-compose.yml logs postgres
```

#### Worker Not Processing Jobs
```bash
# Check Redis connection
docker-compose -f infra/docker-compose.yml ps redis

# Check worker logs
docker-compose -f infra/docker-compose.yml logs worker

# Restart worker
docker-compose -f infra/docker-compose.yml restart worker
```

#### Client Build Issues
```bash
# Clear node_modules and reinstall
cd client
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 18+
npm --version
```

#### Import/Module Errors
```bash
# Reinstall Python dependencies
cd server
rm -rf __pycache__ *.pyc
pip install -e .[dev,nlp]

# Check Python version
python --version  # Should be 3.9+
```

### Logs and Debugging

#### View Application Logs
```bash
# Server logs
docker-compose -f infra/docker-compose.yml logs -f server

# Worker logs
docker-compose -f infra/docker-compose.yml logs -f worker

# All logs
docker-compose -f infra/docker-compose.yml logs -f
```

#### Check Health Endpoints
```bash
# API health
curl http://localhost:8000/health

# Database connectivity
curl http://localhost:8000/healthz
```

#### View Metrics (Development Only)
```bash
curl http://localhost:8000/metrics
```

### Performance Issues

#### High Memory Usage
- Reduce batch sizes in environment variables
- Use VADER instead of Hugging Face models
- Check for memory leaks in worker processes

#### Slow API Responses
- Check database query performance
- Monitor Redis queue length
- Review worker processing times in metrics

#### Client Freezing
- Clear browser cache
- Check network connectivity
- Review browser console for JavaScript errors

### Getting Help

1. Check this README and troubleshooting section
2. Review GitHub Issues for similar problems
3. Check logs using the commands above
4. Create a new issue with:
   - Full error messages
   - Steps to reproduce
   - Environment details (`docker --version`, `python --version`, etc.)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Quick Links:**
- [API Documentation](http://localhost:8000/docs)
- [Contributing Guide](CONTRIBUTING.md)
- [Architecture Details](docs/architecture.md)
- [API Reference](docs/api.md)
