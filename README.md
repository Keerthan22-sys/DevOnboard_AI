# DevOnboard AI

Privacy-first AI-powered developer onboarding platform. Ingest project documentation (PDFs, Confluence, GitHub repos, Markdown) into a RAG pipeline, then ask questions and get source-attributed answers grounded in your project's knowledge base.

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your settings

# 2. Start all services
docker compose up --build

# 3. Pull the LLM model (first time only, takes 5-15 min)
docker exec -it ollama ollama pull llama3.1:8b

# 4. Run database migrations
docker exec -it devonboard-backend alembic upgrade head
```

**Services:**
| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

## Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic
- **Frontend:** Next.js 14, TypeScript, shadcn/ui, Tailwind CSS
- **RAG:** LlamaIndex, sentence-transformers, ChromaDB
- **LLM:** Ollama (Llama 3.1 8B) — fully local, no data leaves your machine
- **Database:** PostgreSQL 16
- **Auth:** JWT + bcrypt

## Development

### Backend (standalone)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend (standalone)
```bash
cd frontend
npm install
npm run dev
```

### Tests
```bash
cd backend
pytest -v
```

## Project Structure

```
├── backend/          # FastAPI + RAG pipeline
│   ├── app/
│   │   ├── api/          # Route handlers
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic
│   │   │   ├── ingestion/    # Document parsing & chunking
│   │   │   ├── rag/          # Retrieval, reranking, prompts
│   │   │   └── llm/          # Ollama client
│   │   └── utils/        # Auth, file handling, source mapping
│   └── alembic/          # Database migrations
├── frontend/         # Next.js 14 App Router
│   └── src/
│       ├── app/          # Pages (login, dashboard, project workspace)
│       ├── components/   # Chat, documents, dashboard, layout
│       └── lib/          # API client, auth context, types
├── docs/             # PRD, architecture, skill references
├── scripts/          # Seed data, demo prep
└── docker/           # Ollama & ChromaDB config
```
