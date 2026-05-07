#!/bin/bash
# scripts/start.sh — First-time setup

echo "Starting DevOnboard AI..."

# Start infrastructure
docker compose up -d postgres chromadb ollama

# Wait for services
echo "Waiting for PostgreSQL..."
until docker compose exec postgres pg_isready -U devonboard; do sleep 2; done

echo "Waiting for ChromaDB..."
until curl -sf http://localhost:8001/api/v1/heartbeat; do sleep 2; done

# Pull Ollama model (first time only)
echo "Pulling LLM model (this may take a while on first run)..."
docker compose exec ollama ollama pull llama3.1:8b

# Run database migrations
echo "Running database migrations..."
docker compose exec backend alembic upgrade head

# Start all services
docker compose up -d

echo "DevOnboard AI is ready!"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
