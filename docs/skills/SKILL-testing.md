---
name: testing-qa
description: "Testing and quality assurance for DevOnboard AI. Use this skill for writing tests, debugging issues, verifying endpoints, testing the RAG pipeline, checking Docker health, and preparing demo data. Triggers on any mention of test, debug, verify, check, QA, demo prep, seed data, or health check."
---

# Testing & QA — DevOnboard AI

## Backend Testing — pytest

```bash
# Install test deps
pip install pytest pytest-asyncio httpx

# Run tests
cd backend && pytest -v
```

### Test Structure
```
backend/tests/
├── conftest.py          # Shared fixtures (test db, client, auth)
├── test_auth.py
├── test_projects.py
├── test_documents.py
├── test_chat.py
└── test_rag/
    ├── test_chunking.py
    ├── test_embeddings.py
    └── test_retriever.py
```

### Test Fixtures

```python
# backend/tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.fixture
async def auth_headers(client):
    """Register a test user and return auth headers."""
    res = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "name": "Test User",
        "password": "testpass123",
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

### API Endpoint Tests

```python
# backend/tests/test_auth.py
import pytest

@pytest.mark.asyncio
async def test_register(client):
    res = await client.post("/api/auth/register", json={
        "email": "new@example.com",
        "name": "New User",
        "password": "password123",
    })
    assert res.status_code == 201
    assert "access_token" in res.json()

@pytest.mark.asyncio
async def test_login(client, auth_headers):
    res = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123",
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

@pytest.mark.asyncio
async def test_me(client, auth_headers):
    res = await client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "test@example.com"
```

## Quick Verification Commands

Run these after each milestone to verify things work:

```bash
# 1. Check all containers are healthy
docker compose ps

# 2. Check backend health
curl http://localhost:8000/api/health

# 3. Check ChromaDB
curl http://localhost:8001/api/v1/heartbeat

# 4. Check Ollama has model
curl http://localhost:11434/api/tags | python -m json.tool

# 5. Check PostgreSQL tables exist
docker compose exec postgres psql -U devonboard -c "\dt"

# 6. Test auth flow
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","name":"Test","password":"test123"}'

# 7. Test file upload (after auth)
TOKEN="<token_from_step_6>"
curl -X POST http://localhost:8000/api/projects/<id>/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.pdf"

# 8. Test chat (after upload)
curl -X POST http://localhost:8000/api/projects/<id>/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is this project about?"}'
```

## Demo Data Seed Script

```python
# scripts/seed_data.py
"""Seed the database with demo data for the presentation."""
import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def seed():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        # 1. Register admin user
        res = await client.post("/api/auth/register", json={
            "email": "keerthan@mhp.com",
            "name": "Keerthan",
            "password": "demo2026",
        })
        token = res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create demo project
        res = await client.post("/api/projects", json={
            "name": "Think Tank Platform",
            "description": "MHP's internal knowledge management platform",
        }, headers=headers)
        project_id = res.json()["id"]

        print(f"Project created: {project_id}")
        print(f"Token: {token}")
        print("Now upload documents via the UI or API")

if __name__ == "__main__":
    asyncio.run(seed())
```

## Demo Prep Checklist

Before the demo with Avinash and Prakash:

- [ ] All Docker containers running (`docker compose ps` — all healthy)
- [ ] Ollama model pulled and responding
- [ ] Demo user account created
- [ ] Demo project with 15-20 documents uploaded
- [ ] Test all 5 demo questions from PRD Section 8
- [ ] Verify source citations are clickable
- [ ] Check response time < 10 seconds
- [ ] Dark mode looks clean
- [ ] Backup: screen recording of full demo flow
