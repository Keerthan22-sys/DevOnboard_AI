# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DevOnboard AI is a privacy-first AI-powered developer onboarding platform. It ingests project docs (PDFs, Confluence, GitHub repos, Markdown) into a RAG pipeline so new developers can ask questions and get source-attributed answers.

**Status:** Active MVP development — 2-week sprint. Project scaffolded, no app code yet.
**Author:** Keerthan (AI Product Manager / GenAI Engineer / Full-Stack Dev) at MHP.

## Design Documents & Skills

```
docs/
├── PRD_DevOnboard_AI.md              # Source of truth: MVP scope, DB schema, API spec, UI spec, demo script
├── devonboard-ai-architecture.md     # Enterprise architecture (reference only — do NOT implement)
└── skills/
    ├── SKILL-backend.md              # FastAPI patterns: models, schemas, endpoints, deps, config
    ├── SKILL-rag.md                  # RAG pipeline: parsers, chunking, embeddings, retriever, chain
    ├── SKILL-frontend.md             # Next.js patterns: types, API client, auth context, components
    ├── SKILL-docker.md               # Docker Compose, Dockerfiles, .env, startup script
    └── SKILL-testing.md              # pytest fixtures, API tests, verification commands, demo prep
```

- PRD Section 5.1 defines the hard MVP boundary. Section 6 governs all MVP decisions.
- The architecture doc is for reference/future only — do NOT implement production features from it.
- **SKILL files contain exact code patterns and templates** — read the relevant skill before implementing any module.

## Critical Rules

1. **MVP ONLY.** Use ChromaDB, local filesystem, JWT/bcrypt, synchronous processing, single workspace. Do NOT use Keycloak, Qdrant, MinIO, Kubernetes, or Celery.
2. **All API responses** must use shape: `{"success": bool, "data": ..., "error": str | null}`
3. **Check requirements.txt / package.json** before installing any package. No duplicates.
4. **Every Python file** must have `from __future__ import annotations` and full type hints.
5. **Pydantic v2** for all schemas — use `model_config` dict, not `class Config`.
6. **Build incrementally.** Build 1 module → test → move on. Don't batch 5 files.
7. **Commit format:** `feat(scope): description` or `fix(scope): description`
8. **No streaming** for MVP. Full response only (streaming is v2).

## MVP Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| Frontend | Next.js 14 (App Router), TypeScript (strict), shadcn/ui, Tailwind |
| RAG | LlamaIndex, sentence-transformers (all-MiniLM-L6-v2) |
| Vector DB | ChromaDB (embedded mode, persistent) |
| LLM | Ollama (local) — Llama 3.1 8B or Mistral 7B |
| Database | PostgreSQL 16 |
| Auth | JWT + bcrypt (passlib) |
| Infra | Docker Compose |

## Commands

### Full stack
```bash
docker compose up              # Start all services
docker compose up --build      # Rebuild and start
docker compose down            # Stop all services
```

### Backend (inside backend/ directory)
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Tests
pytest                         # Run all tests
pytest tests/test_auth.py      # Run single test file
pytest -k "test_login"         # Run tests matching name
```

### Frontend (inside frontend/ directory)
```bash
npm install
npm run dev                    # Dev server on port 3000
npm run build                  # Production build
npm run lint                   # Lint check
```

### Ollama (after first container start)
```bash
docker exec -it ollama ollama pull llama3.1:8b
```

## Architecture — Key Patterns

### Data Flow: Document Ingestion
Upload/URL → Parser (pdf/md/confluence/github) → ChunkingEngine (1000 tokens, 200 overlap) → sentence-transformers embedding → ChromaDB collection `project_{project_id}` + PostgreSQL `document_chunks` → document status = 'ready'

### Data Flow: Chat Query
Question → embedding → ChromaDB top_k=10 → cross-encoder rerank → top 5 → prompt construction → Ollama → source citation mapping → response with sources array

### LLM Performance Optimizations
- **Response cache:** In-memory LRU (128 entries) in `ollama_client.py` — identical prompts return instantly.
- **`keep_alive: "10m"`:** Ollama keeps model in memory between requests, eliminating cold-start (~4s).
- **Model preload:** FastAPI lifespan calls `preload_model()` on startup so the model is warm before first query.
- **Reusable httpx client:** Single module-level `AsyncClient` with 300s timeout (local LLM can be slow on CPU).
- **HyDE toggle:** `HYDE_ENABLED` env var (default `false`). When disabled, skips the hypothetical-answer LLM call, halving query latency.

### Backend Layering
- `api/` — FastAPI route handlers. Thin layer: validate input, call service, return response.
- `api/deps.py` — Shared dependencies: `get_db` (async session), `get_current_user` (JWT).
- `services/ingestion/` — Document parsing and chunking. Each source type has its own parser.
- `services/rag/` — Retrieval, reranking, prompt construction, orchestration (`chain.py`).
- `services/llm/` — Ollama HTTP client and model config.
- `models/` — SQLAlchemy ORM models. Schema is defined in PRD — do not modify columns without approval.
- `schemas/` — Pydantic v2 request/response models.
- `utils/auth.py` — JWT create/verify, password hashing with passlib.

### Frontend Layering
- `lib/api.ts` — Axios client with JWT interceptor (attaches token to all requests).
- `lib/auth.ts` — React Context for auth state + hooks.
- `components/ui/` — shadcn/ui primitives.
- App Router: Server Components by default, `'use client'` only when interactivity is needed.
- Next.js `rewrites` in `next.config.js` proxies `/api` → `backend:8000`.
- Dark mode first — use CSS variables.

### ChromaDB Collection Naming
Collections are `project_{uuid}` with hyphens replaced by underscores:
`project_550e8400_e29b_41d4_a716_446655440000`

## Common Pitfalls

- **CORS:** FastAPI must have CORS middleware allowing `localhost:3000`.
- **Alembic async:** Use `run_async` in `env.py` for SQLAlchemy 2.0 async.
- **File uploads:** Requires `python-multipart` package.
- **ChromaDB persistence:** Must mount a Docker volume — never use in-memory mode.
- **Ollama pull:** Model must be pulled after container first starts (not automatic).

## Build Order

Follow the sprint plan in PRD Section 6 exactly. Summary:
1. Scaffold + Docker Compose + .env
2. Database models + Alembic migrations
3. Auth (JWT, endpoints, schemas)
4. Ingestion pipeline (parsers, chunking, embeddings)
5. RAG engine (retriever, reranker, chain, chat endpoint)
6. Frontend (auth pages, dashboard, document upload, chat UI)
7. GitHub integration
8. Polish + demo prep
