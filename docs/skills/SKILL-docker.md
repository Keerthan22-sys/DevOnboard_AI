---
name: docker-infra
description: "Docker and infrastructure setup for DevOnboard AI. Use for Docker Compose configuration, Dockerfiles, container orchestration, service health checks, volume management, environment variables, and deployment. Triggers on any mention of Docker, container, compose, Dockerfile, deployment, infrastructure, or services setup."
---

# Docker Infrastructure — DevOnboard AI

## docker-compose.yml — Complete MVP

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: devonboard
      POSTGRES_USER: devonboard
      POSTGRES_PASSWORD: ${DB_PASSWORD:-devonboard_secret}
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U devonboard"]
      interval: 5s
      timeout: 5s
      retries: 5

  chromadb:
    image: chromadb/chroma:0.5.23
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma
    environment:
      ANONYMIZED_TELEMETRY: "false"
      ALLOW_RESET: "true"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 10s
      timeout: 5s
      retries: 3

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 15s
      timeout: 10s
      retries: 3

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://devonboard:${DB_PASSWORD:-devonboard_secret}@postgres:5432/devonboard
      CHROMA_HOST: chromadb
      CHROMA_PORT: 8000
      OLLAMA_HOST: http://ollama:11434
      OLLAMA_MODEL: ${OLLAMA_MODEL:-llama3.1:8b}
      JWT_SECRET: ${JWT_SECRET:-change-me-in-production}
      UPLOAD_DIR: /app/uploads
      REPO_DIR: /app/repos
      EMBEDDING_MODEL: all-MiniLM-L6-v2
    volumes:
      - upload_data:/app/uploads
      - repo_data:/app/repos
    depends_on:
      postgres:
        condition: service_healthy
      chromadb:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on:
      - backend

volumes:
  pg_data:
  chroma_data:
  ollama_data:
  upload_data:
  repo_data:
```

## Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads /app/repos

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

## Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
```

## .env.example

```bash
# Database
DB_PASSWORD=devonboard_secret

# JWT
JWT_SECRET=your-super-secret-key-change-in-production

# Ollama
OLLAMA_MODEL=llama3.1:8b

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Startup Script

```bash
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
```

## Common Docker Issues

- **Ollama GPU**: If no NVIDIA GPU, remove the `deploy.resources` block from ollama service
- **ChromaDB port**: ChromaDB listens on 8000 internally, mapped to 8001 externally. Backend connects on port 8000 (internal Docker network)
- **Volume permissions**: If upload fails, check volume mount permissions
- **Hot reload**: Backend uses `--reload` flag. Frontend uses Next.js dev server. Both watch for file changes.
- **First startup**: Ollama model pull takes 5-15 minutes. Be patient.
