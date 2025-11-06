#!/bin/bash

# Development environment setup
set -e

echo "🔧 Setting up development environment..."

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Install Python dependencies for development
cd server
pip install -e ".[dev]"
cd ..

cd worker
pip install -e .
cd ..

# Install Node.js dependencies
cd client
npm install
cd ..

echo "✅ Development environment ready!"
echo ""
echo "Available commands:"
echo "  make dev        - Start all development servers"
echo "  make test       - Run tests"
echo "  make lint       - Run linting"
echo "  make format     - Format code"
