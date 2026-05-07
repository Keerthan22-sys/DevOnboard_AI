from __future__ import annotations

import logging

import httpx

from app.config import settings
from app.services.cache.cache_manager import CacheNamespace, cache_get, cache_set

logger = logging.getLogger(__name__)

# Module-level HTTP client for connection reuse
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    """Return a reusable async HTTP client with generous timeout."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=settings.OLLAMA_HOST,
            timeout=httpx.Timeout(300.0, connect=10.0),
        )
    return _client


async def generate_response(
    prompt: str,
    system_prompt: str,
    model: str | None = None,
    project_id: str | None = None,
) -> str:
    """Call Ollama API and return the full response.

    Cache strategy:
    - Key: hash of (model, system_prompt, prompt)
    - TTL: CACHE_TTL_LLM (default 1 hour)
    - Indexed by project_id so cache is invalidated when docs change.
    - Falls back to direct Ollama call if Redis is unavailable.
    """
    model = model or settings.OLLAMA_MODEL

    # Check Redis cache
    cached = await cache_get(CacheNamespace.LLM, model, system_prompt, prompt)
    if cached is not None:
        logger.info("[LLM Cache] HIT — skipping Ollama call")
        return cached

    client = _get_client()
    response = await client.post(
        "/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 2048,
            },
        },
    )
    response.raise_for_status()
    answer = response.json()["response"]

    # Store in Redis cache (fire-and-forget, failure is non-fatal)
    await cache_set(
        CacheNamespace.LLM,
        model, system_prompt, prompt,
        value=answer,
        project_id=project_id,
    )

    return answer


async def check_ollama_health() -> bool:
    """Check if Ollama is running and model is available."""
    # Check cached health status first
    cached = await cache_get(CacheNamespace.HEALTH, "ollama", settings.OLLAMA_MODEL)
    if cached is not None:
        return cached == "true"

    try:
        client = _get_client()
        resp = await client.get("/api/tags")
        models = [m["name"] for m in resp.json().get("models", [])]
        healthy = settings.OLLAMA_MODEL in models or any(
            settings.OLLAMA_MODEL.split(":")[0] in m for m in models
        )

        await cache_set(
            CacheNamespace.HEALTH,
            "ollama", settings.OLLAMA_MODEL,
            value=str(healthy).lower(),
        )
        return healthy
    except Exception:
        return False


async def preload_model() -> None:
    """Pre-load the model into Ollama memory so first query is fast."""
    try:
        client = _get_client()
        await client.post(
            "/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": "",
                "keep_alive": "10m",
            },
        )
        logger.info("[Ollama] Model %s pre-loaded into memory", settings.OLLAMA_MODEL)
    except Exception:
        logger.warning("[Ollama] Failed to pre-load model", exc_info=True)
