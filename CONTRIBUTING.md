# Contributing to AI Customer Insights Agent

Thank you for your interest in contributing to the AI Customer Insights Agent! This document provides guidelines and information for contributors.

## 🚀 Quick Start for Contributors

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.9+
- Git

### Setup Development Environment
```bash
# Clone the repository
git clone https://github.com/your-org/feedback-analysis-agent.git
cd feedback-analysis-agent

# Bootstrap project (installs all dependencies)
make bootstrap

# Setup development environment
make dev-setup

# Start services
make docker-up

# Start development servers
make dev
```

### Verify Setup
```bash
# Run tests
make test

# Run linting
make lint

# Check that everything works
curl http://localhost:8001/health
curl http://localhost:3000
```

## 📋 Development Workflow

### 1. Choose an Issue
- Check [GitHub Issues](https://github.com/your-org/feedback-analysis-agent/issues) for open tasks
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to indicate you're working on it

### 2. Create a Branch
```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-number-description
```

### 3. Make Changes
- Follow the existing code style and patterns
- Add tests for new functionality
- Update documentation as needed
- Run tests and linting frequently

### 4. Test Your Changes
```bash
# Run all tests
make test

# Run specific test suites
make test-server
make test-client
make test-worker

# Check code quality
make lint
make format
```

### 5. Commit Changes
```bash
# Stage your changes
git add .

# Commit with descriptive message
git commit -m "feat: add new feature description

- What was changed
- Why it was changed
- How it was tested"

# For multiple commits, use conventional commits
git commit -m "fix: resolve database connection issue"
git commit -m "test: add unit tests for new feature"
git commit -m "docs: update API documentation"
```

### 6. Push and Create Pull Request
```bash
# Push your branch
git push origin feature/your-feature-name

# Create a Pull Request on GitHub
# - Use a clear title
# - Provide detailed description
# - Reference related issues
# - Request review from maintainers
```

## 🧪 Testing Guidelines

### Test Coverage Requirements
- **Server**: Minimum 80% coverage across all modules
- **Client**: Minimum 80% coverage across all components
- **Worker**: Minimum 80% coverage for task processing

### Running Tests
```bash
# All tests with coverage
make test

# Individual test suites
make test-server  # Server tests
make test-client  # Client tests
make test-worker  # Worker tests

# Logging tests
make test-logging
```

### Test Structure
- **Unit Tests**: Test individual functions and components in isolation
- **Integration Tests**: Test component interactions and API endpoints
- **End-to-End Tests**: Test complete user workflows

### Test Examples
```python
# Server test example
def test_create_feedback_success():
    # Arrange
    feedback_data = {"text": "Great product!", "source": "website"}

    # Act
    response = client.post("/api/feedback", json=feedback_data)

    # Assert
    assert response.status_code == 201
    assert "id" in response.json()
```

```typescript
// Client test example
describe('KPICards', () => {
  it('renders loading state correctly', () => {
    render(<KPICards />)
    expect(screen.getByTestId('loading')).toBeInTheDocument()
  })
})
```

## 🛠️ Code Quality Standards

### Python (Server/Worker)
- **Linting**: `black`, `isort`, `flake8`
- **Type Hints**: Use type annotations for all functions
- **Docstrings**: Google-style docstrings for modules and functions
- **Imports**: Group imports (stdlib, third-party, local)

```python
# Good: Proper imports and type hints
from typing import List, Optional
from fastapi import APIRouter, HTTPException

def process_feedback(text: str, source: Optional[str] = None) -> dict:
    """Process customer feedback text.

    Args:
        text: The feedback text to process
        source: Optional source identifier

    Returns:
        Processed feedback data
    """
    pass
```

### TypeScript (Client)
- **Linting**: ESLint with React and TypeScript rules
- **Type Safety**: Strict TypeScript configuration
- **Component Structure**: Functional components with hooks

```typescript
// Good: Proper TypeScript usage
interface FeedbackItem {
  id: string
  text: string
  sentiment: number
  source: string
}

const FeedbackCard: React.FC<{ item: FeedbackItem }> = ({ item }) => {
  return (
    <div className="feedback-card">
      <h3>{item.text}</h3>
      <span>Sentiment: {item.sentiment}</span>
    </div>
  )
}
```

### Commit Message Conventions
Use [Conventional Commits](https://conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Maintenance

**Examples:**
```
feat: add sentiment analysis endpoint
fix: resolve memory leak in worker process
docs: update API documentation
test: add integration tests for feedback processing
```

## 🏗️ Architecture Guidelines

### Server Architecture
- **FastAPI**: Use dependency injection for database sessions
- **SQLAlchemy**: Use async sessions and proper transaction management
- **Pydantic**: Validate all input/output models
- **Structured Logging**: Include request_id in all log entries

### Client Architecture
- **React**: Functional components with hooks
- **Zustand**: State management for global state
- **React Query**: Server state management
- **TypeScript**: Strict type checking enabled

### Worker Architecture
- **RQ**: Queue-based job processing
- **Error Handling**: Comprehensive error logging and metrics
- **Resource Management**: Proper cleanup and monitoring

## 🔒 Security Guidelines

### General Security
- **Input Validation**: Validate all user inputs on server and client
- **SQL Injection**: Use parameterized queries or ORMs
- **XSS Prevention**: Sanitize user content in templates
- **Authentication**: Implement proper auth for sensitive endpoints

### API Security
```python
# Server: Input validation with Pydantic
from pydantic import BaseModel, validator

class FeedbackCreate(BaseModel):
    text: str
    source: str

    @validator('text')
    def text_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be empty')
        return v
```

### Environment Variables
- **Never commit secrets** to version control
- **Use .env files** for local development
- **Document all environment variables** in README
- **Validate required variables** at startup

## 📚 Documentation Standards

### Code Documentation
- **README.md**: Comprehensive setup and usage guide
- **API Docs**: Auto-generated from FastAPI
- **Inline Comments**: Explain complex logic
- **Docstrings**: For all public functions and classes

### Pull Request Template
When creating a PR, include:
- **Description**: What changes were made and why
- **Testing**: How the changes were tested
- **Screenshots**: UI changes with before/after
- **Breaking Changes**: Any breaking changes
- **Checklist**: Completed contribution checklist

## 🚨 Issue Reporting

### Bug Reports
Include:
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Environment details** (OS, versions, etc.)
- **Logs and error messages**
- **Screenshots** (if applicable)

### Feature Requests
Include:
- **Problem statement**
- **Proposed solution**
- **Alternative solutions considered**
- **Additional context**

## 📞 Getting Help

### Communication Channels
- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Pull Request Comments**: For code review feedback

### Review Process
1. **Automated Checks**: CI must pass (tests, linting, coverage)
2. **Code Review**: At least one maintainer review required
3. **Testing**: Manual testing may be requested for complex changes
4. **Approval**: Maintainers will approve and merge

### Recognition
Contributors will be:
- Listed in CHANGELOG.md for significant contributions
- Acknowledged in release notes
- Invited to become maintainers for sustained contributions

## 🎉 Recognition

We appreciate all contributions, big and small! Contributors may be recognized through:
- GitHub contributor statistics
- CHANGELOG.md entries
- Release notes acknowledgment
- Maintainer status invitation

Thank you for contributing to the AI Customer Insights Agent! 🚀
