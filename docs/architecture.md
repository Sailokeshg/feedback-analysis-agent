# Architecture Overview

## System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        A[React Dashboard<br/>localhost:3000]
        A1[TypeScript + Vite]
        A2[Zustand State Management]
        A3[React Query]
        A4[Recharts Visualizations]
    end

    subgraph "API Gateway Layer"
        B[FastAPI Server<br/>localhost:8000]
        B1[Request Timing Middleware]
        B2[Structured Logging]
        B3[Rate Limiting]
        B4[CORS Handling]
    end

    subgraph "Service Layer"
        C[Sentiment Service]
        D[Clustering Service]
        E[Embedding Service]
        F[Query Service]
        G[Analytics Service]
    end

    subgraph "Data Layer"
        H[(PostgreSQL<br/>localhost:5432)]
        I[(Redis Queue<br/>localhost:6379)]
        J[(Chroma Vector DB<br/>localhost:8000)]
    end

    subgraph "Worker Layer"
        K[RQ Worker Process]
        K1[Batch Processing]
        K2[ML Model Inference]
        K3[Background Tasks]
    end

    subgraph "Infrastructure Layer"
        L[Docker Compose]
        M[GitHub Actions CI/CD]
        N[Monitoring & Metrics]
        O[Health Checks]
    end

    A --> B
    B --> C
    B --> D
    B --> E
    B --> F
    B --> G

    C --> H
    D --> H
    E --> H
    F --> H
    G --> H

    B --> I
    I --> K

    E --> J
    K --> J

    K --> H
    K --> J

    L --> H
    L --> I
    L --> J
    L --> K

    M --> L
    N --> B
    N --> K
    O --> B

    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style K fill:#e8f5e8
    style N fill:#fff3e0
    style O fill:#ffebee
```

## Component Details

### Client Layer

**React Dashboard (localhost:3000)**
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development
- **State Management**:
  - Zustand for global application state
  - React Query for server state management
- **UI Components**: Recharts for data visualization
- **Styling**: Tailwind CSS
- **Features**:
  - Real-time dashboard with KPIs
  - Interactive charts and graphs
  - Chat interface for Q&A
  - File upload for batch processing

### API Gateway Layer

**FastAPI Server (localhost:8000)**
- **Framework**: FastAPI with automatic OpenAPI docs
- **Middleware Stack**:
  - Request timing and logging
  - Rate limiting
  - CORS handling
  - Structured logging with request IDs
- **Validation**: Pydantic models for all I/O
- **Authentication**: JWT-based auth (future)
- **Monitoring**: Prometheus metrics endpoint

### Service Layer

**Core Services**:
- **SentimentService**: VADER/HuggingFace sentiment analysis
- **ClusteringService**: Topic clustering with HDBSCAN/UMAP
- **EmbeddingService**: Sentence transformers for vectorization
- **QueryService**: Agentic Q&A using vector search
- **AnalyticsService**: KPI calculation and trend analysis

**Architecture Patterns**:
- Dependency injection for testability
- Strategy pattern for ML model selection
- Repository pattern for data access
- Service layer for business logic

### Data Layer

**Databases**:
- **PostgreSQL**: Primary relational database
  - Feedback items and metadata
  - User sessions and auth
  - Topic classifications
  - Audit logs
- **Redis**: Caching and job queues
  - RQ job queue management
  - Session caching
  - Rate limiting data
- **Chroma**: Vector database for embeddings
  - Semantic search indexing
  - Feedback similarity matching

### Worker Layer

**RQ Worker Process**:
- **Job Types**:
  - Feedback batch processing
  - ML model inference
  - Data aggregation jobs
  - Report generation
- **Monitoring**:
  - Job duration histograms
  - Success/failure metrics
  - Active job tracking
- **Error Handling**:
  - Comprehensive logging
  - Automatic retries
  - Dead letter queues

### Infrastructure Layer

**Docker Compose**:
- **Services**: postgres, redis, chroma, server, worker, client
- **Networking**: Isolated networks for security
- **Volumes**: Persistent data storage
- **Health Checks**: Automatic service monitoring

**CI/CD Pipeline**:
- **GitHub Actions**: Automated testing and deployment
- **Coverage**: 80%+ test coverage requirement
- **Linting**: Code quality enforcement
- **Security**: Dependency vulnerability scanning

## Data Flow

### Feedback Processing Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant C as Client
    participant A as API
    participant Q as Queue
    participant W as Worker
    participant DB as Database
    participant V as Vector DB

    U->>C: Upload feedback file
    C->>A: POST /api/upload/csv
    A->>DB: Store raw feedback
    A->>Q: Queue processing job
    Q->>W: Process job
    W->>W: Sentiment analysis
    W->>W: Topic clustering
    W->>W: Generate embeddings
    W->>DB: Update feedback records
    W->>V: Store embeddings
    W->>Q: Mark job complete
```

### Query Processing Flow

```mermaid
sequenceDiagram
    participant U as User
    participant C as Client
    participant A as API
    participant V as Vector DB
    participant M as ML Models

    U->>C: Ask question
    C->>A: POST /api/query/chat
    A->>V: Semantic search
    A->>M: Generate response
    A->>C: Return answer
    C->>U: Display response
```

## Security Architecture

### Authentication & Authorization
- JWT-based authentication (planned)
- Role-based access control
- API key management for external integrations

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- XSS protection in client
- Secure environment variable handling

### Network Security
- Docker network isolation
- CORS policy enforcement
- Rate limiting middleware
- Request size limits

## Monitoring & Observability

### Metrics
- **HTTP Metrics**: Request counts, duration, error rates
- **Business Metrics**: Feedback processed, user engagement
- **System Metrics**: CPU, memory, disk usage
- **Worker Metrics**: Job success rates, processing times

### Logging
- **Structured JSON logs** with request tracing
- **Request IDs** for distributed tracing
- **Log levels**: DEBUG, INFO, WARNING, ERROR
- **Log aggregation**: File rotation and retention

### Health Checks
- **Application health**: /health endpoint
- **Database connectivity**: /healthz endpoint
- **Dependency checks**: External service availability
- **Metrics endpoint**: /metrics (development only)

## Deployment Architecture

### Development Environment
- Local Docker Compose setup
- Hot reloading for development
- Debug logging enabled
- Metrics endpoint exposed

### Production Environment (Future)
- Kubernetes deployment
- Load balancer configuration
- Horizontal scaling
- Production logging and monitoring
- Database connection pooling
- Redis clustering

## Performance Characteristics

### Scalability
- **Horizontal scaling**: Stateless API servers
- **Queue-based processing**: Async job handling
- **Database optimization**: Connection pooling, indexing
- **Caching strategy**: Redis for session and query caching

### Performance Targets
- **API Response Time**: <500ms for 95th percentile
- **Worker Job Duration**: <30 seconds average
- **Concurrent Users**: 100+ simultaneous connections
- **Feedback Processing**: 1000 items/minute

## Future Enhancements

### Planned Architecture Improvements
- **Microservices decomposition**
- **Event-driven architecture**
- **GraphQL API** for flexible queries
- **Real-time WebSocket connections**
- **Advanced ML model serving**
- **Multi-region deployment**
- **Advanced security features**
