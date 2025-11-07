# AI Customer Insights Agent - Development Makefile

.PHONY: help dev build test test-server test-worker test-client demo-logging test-logging lint format clean bootstrap docker-up docker-down

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

bootstrap: ## Bootstrap the project (install dependencies, setup services)
	./scripts/bootstrap.sh

dev-setup: ## Setup development environment
	./scripts/dev-setup.sh

dev: ## Start development servers
	@echo "Starting development servers..."
	@docker-compose -f infra/docker-compose.yml up -d postgres redis chroma
	@sleep 5
	@echo "Starting server..."
	@cd server && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
	@echo "Starting worker..."
	@cd worker && python run_worker.py &
	@echo "Starting client..."
	@cd client && npm run dev &
	@echo "Development servers started!"
	@echo "Client: http://localhost:3000"
	@echo "Server: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

build: ## Build all services
	docker-compose -f infra/docker-compose.yml build

test: ## Run all tests with coverage
	@echo "Running server tests with coverage..."
	cd server && python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=xml --cov-fail-under=80
	@echo "Running worker tests with coverage..."
	cd worker && python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=xml --cov-fail-under=80
	@echo "Running client tests with coverage..."
	cd client && npm run test:coverage

test-server: ## Run server tests only
	cd server && python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=xml --cov-fail-under=80

test-worker: ## Run worker tests only
	cd worker && python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=xml --cov-fail-under=80

test-client: ## Run client tests only
	cd client && npm run test:coverage

demo-logging: ## Run logging and metrics demonstration
	cd server && python demo_logging_metrics.py

test-logging: ## Run logging and metrics integration tests
	cd server && python test_logging_metrics.py

lint: ## Run linting
	@echo "Linting Python code..."
	cd server && black --check . && isort --check-only . && flake8 .
	@echo "Linting TypeScript/JavaScript..."
	cd client && npm run lint

format: ## Format code
	@echo "Formatting Python code..."
	cd server && black . && isort .
	@echo "Formatting TypeScript/JavaScript..."
	cd client && npm run format

docker-up: ## Start all Docker services
	docker-compose -f infra/docker-compose.yml up -d

docker-down: ## Stop all Docker services
	docker-compose -f infra/docker-compose.yml down

clean: ## Clean up development artifacts
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name node_modules -exec rm -rf {} +
	find . -type d -name dist -exec rm -rf {} +
	find . -name "*.pyc" -delete
	docker-compose -f infra/docker-compose.yml down -v
