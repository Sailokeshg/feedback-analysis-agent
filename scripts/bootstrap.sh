#!/bin/bash

# Bootstrap script for AI Customer Insights Agent
set -e

echo "🚀 Bootstrapping AI Customer Insights Agent..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "📦 Installing Python dependencies..."

# Install server dependencies
cd server
source venv/bin/activate
pip install -e .
cd ..

# Install worker dependencies
cd worker
pip install -e .
cd ..

echo "📦 Installing Node.js dependencies..."
cd client
npm install
cd ..

echo "🐳 Starting Docker services..."
docker-compose -f infra/docker-compose.yml up -d postgres redis chroma

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "✅ Bootstrap complete!"
echo ""
echo "To start the full stack:"
echo "  docker-compose -f infra/docker-compose.yml up"
echo ""
echo "To start development servers:"
echo "  Client: cd client && npm run dev"
echo "  Server: cd server && uvicorn app.main:app --reload"
echo "  Worker: cd worker && python run_worker.py"
