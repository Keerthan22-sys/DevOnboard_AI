# DevOnboard AI — Tech Stack & Architecture Analysis

## Tech Stack Overview

| Layer | Technology |
| ----- | --------- |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| **Frontend** | Next.js 14 (App Router), TypeScript (strict), Tailwind CSS, shadcn/ui, Framer Motion |
| **Database** | PostgreSQL 16 (asyncpg driver) |
| **Vector DB** | ChromaDB 0.5.23 (persistent mode, cosine distance) |
| **LLM** | Ollama (local) — Llama 3.1 8B default, configurable |
| **Embeddings** | all-MiniLM-L6-v2 (384-dim, sentence-transformers) |
| **Reranker** | cross-encoder/ms-marco-MiniLM-L-6-v2 |
| **Auth** | JWT (HS256) + bcrypt (passlib) |
| **Infra** | Docker Compose (6 services) |

---

## RAG Architecture (3-Stage Retrieval)

### Ingestion Pipeline

1. **Parse** — PDF (pdfplumber), Markdown (heading-aware), Confluence (REST API + HTML scraping), GitHub/GitLab (shallow clone, priority file indexing)
2. **Clean** — Strip HTML, base64 blobs, normalize whitespace (`text_cleaner.py`)
3. **Chunk** — LangChain `RecursiveCharacterTextSplitter` with tiktoken, 1000 tokens / 200 overlap, boundary-aware separators (Markdown headings → paragraphs → sentences)
4. **Embed** — `all-MiniLM-L6-v2`, prepends doc title + section title for context
5. **Store** — ChromaDB collection `project_{uuid}` + PostgreSQL `document_chunks` table

### Query Pipeline (`chain.py`)

1. **HyDE** (optional, off by default) — LLM generates a hypothetical doc answer, embedded as an additional query vector
2. **Multi-Query Recall** — Embeds original query + HyDE hypothesis, queries ChromaDB with both, unions top 20 results
3. **Deduplication** — Content hash prefix matching removes duplicates
4. **Cross-Encoder Reranking** — `ms-marco-MiniLM-L-6-v2` re-scores all candidates with full token attention, selects top 5
5. **Prompt Construction** — System prompt + 5 context chunks + user question
6. **Generation** — Ollama (full response, no streaming), `temperature: 0.1`, `num_predict: 2048`
7. **Source Citation** — Maps chunk metadata (doc title, page #, section, URL) to response sources array

---

## LLM Configuration (`ollama_client.py`)

- **Provider:** Local Ollama via HTTP (`/api/generate`)
- **Model:** `llama3.1:8b` (configurable via env)
- **Key optimizations:**
  - Model preloading on FastAPI startup (`keep_alive: 10m` keeps model in GPU/RAM)
  - Redis-backed response cache with TTL (replaces in-memory LRU)
  - Reusable `httpx.AsyncClient` with 300s timeout
  - HyDE toggle (`HYDE_ENABLED=false` by default) — disabling halves query latency

---

## High-Level System Design

```text
┌─────────────┐     /api proxy     ┌──────────────────┐
│  Next.js 14 │ ──────────────────→│   FastAPI (8000)  │
│  (port 3000)│                    │                   │
│  App Router │                    │  ┌─── API Layer   │
│  shadcn/ui  │                    │  ├─── Services    │
│  Axios+JWT  │                    │  │  ├─ Ingestion  │──→ Parse/Chunk/Embed
└─────────────┘                    │  │  ├─ RAG        │──→ Retrieve/Rerank/Generate
                                   │  │  ├─ LLM        │──→ Ollama client + cache
                                   │  │  └─ Cache      │──→ Redis (multi-layer)
                                   │  ├─── Models/ORM  │
                                   │  └─── Auth (JWT)  │
                                   └────────┬──────────┘
                                            │
                       ┌────────────────────┼────────────────────┐
                       ▼                    ▼                    ▼
                ┌────────────┐   ┌────────────────┐   ┌────────────┐
                │ PostgreSQL │   │  ChromaDB       │   │   Ollama   │
                │   (5432)   │   │   (8001)        │   │  (11434)   │
                │ Users,Docs │   │  Vectors        │   │ Llama 3.1  │
                │ Sessions   │   │  384-dim        │   │    8B      │
                └────────────┘   └────────────────┘   └────────────┘
                                        ▲
                                        │
                                 ┌────────────┐
                                 │   Redis    │
                                 │   (6379)   │
                                 │ LLM + RAG  │
                                 │   Cache    │
                                 └────────────┘
```

---

## Key Design Principles

- **Privacy-first** — Fully local LLM, no external API calls
- **Async throughout** — asyncpg + FastAPI for non-blocking I/O
- **Consistent API contract** — All responses use `{success, data, error}` shape
- **Singleton models** — Embedding, reranker, and LLM loaded once to avoid repeated initialization overhead
- **Graceful degradation** — Redis cache failures are silent; app continues without caching
