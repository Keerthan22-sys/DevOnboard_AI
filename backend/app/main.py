from __future__ import annotations

import asyncio
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, credentials, dashboard, documents, projects
from app.services.cache.cache_manager import get_cache_stats
from app.services.cache.redis_client import check_redis_health, close_redis, get_redis
from app.services.llm.ollama_client import preload_model

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup: connect Redis pool + pre-load Ollama model. Shutdown: close Redis."""
    # Warm up Redis connection pool
    try:
        await get_redis()
        healthy = await check_redis_health()
        logger.info("[Startup] Redis connected: %s", healthy)
    except Exception:
        logger.warning("[Startup] Redis unavailable — cache will be bypassed", exc_info=True)

    # Pre-load Ollama model (non-blocking)
    asyncio.create_task(preload_model())

    yield

    # Graceful shutdown
    await close_redis()
    logger.info("[Shutdown] Redis connection pool closed")


app = FastAPI(title="DevOnboard AI", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(documents.router)
app.include_router(credentials.router)
app.include_router(chat.router)
app.include_router(dashboard.router)


@app.get("/api/health")
async def health():
    redis_ok = await check_redis_health()
    return {
        "status": "ok",
        "service": "devonboard-ai",
        "redis": "connected" if redis_ok else "unavailable",
    }


@app.get("/api/cache/stats")
async def cache_stats():
    """Admin endpoint: Redis cache hit rate, memory usage, key count."""
    stats = await get_cache_stats()
    return {"success": True, "data": stats, "error": None}
