from __future__ import annotations

import hashlib
import json
import logging
from enum import Enum

from app.config import settings
from app.services.cache.redis_client import get_redis

logger = logging.getLogger(__name__)


class CacheNamespace(str, Enum):
    """Cache key namespaces — each layer has its own TTL and invalidation rules.

    LLM:        Full prompt → generated answer. Invalidated when project docs change.
    RETRIEVAL:  Query + project → ranked chunk IDs/scores. Invalidated on doc changes.
    HEALTH:     Service health checks (Ollama, ChromaDB). Short TTL, no manual invalidation.
    """
    LLM = "llm"
    RETRIEVAL = "rag"
    HEALTH = "health"


# Map namespace → TTL in seconds
_TTL_MAP: dict[CacheNamespace, int] = {
    CacheNamespace.LLM: settings.CACHE_TTL_LLM,
    CacheNamespace.RETRIEVAL: settings.CACHE_TTL_RETRIEVAL,
    CacheNamespace.HEALTH: settings.CACHE_TTL_HEALTH,
}


def _build_key(namespace: CacheNamespace, *parts: str) -> str:
    """Build a namespaced cache key.

    Format: devonboard:{namespace}:{sha256_hash}
    Using hash prevents key-length issues and keeps Redis memory predictable.
    """
    raw = "::".join(parts)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    return f"{settings.CACHE_KEY_PREFIX}:{namespace.value}:{digest}"


def _project_pattern(namespace: CacheNamespace, project_id: str) -> str:
    """Build a pattern to match all keys for a project in a namespace.

    We store a secondary index (a Redis SET) per project so invalidation
    doesn't rely on SCAN, which is slow and blocks at scale.
    """
    return f"{settings.CACHE_KEY_PREFIX}:idx:{namespace.value}:{project_id}"


async def cache_get(namespace: CacheNamespace, *key_parts: str) -> str | None:
    """Retrieve a cached value. Returns None on miss or if Redis is down.

    This function never raises — cache failures are logged and treated as misses.
    The application always has a working fallback path through the actual services.
    """
    if not settings.CACHE_ENABLED:
        return None
    try:
        client = await get_redis()
        key = _build_key(namespace, *key_parts)
        value = await client.get(key)
        if value is not None:
            logger.debug("[Cache] HIT %s key=%s", namespace.value, key[-12:])
        return value
    except Exception:
        logger.warning("[Cache] GET failed for %s", namespace.value, exc_info=True)
        return None


async def cache_get_json(namespace: CacheNamespace, *key_parts: str) -> dict | list | None:
    """Retrieve and deserialize a JSON-cached value."""
    raw = await cache_get(namespace, *key_parts)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        logger.warning("[Cache] JSON decode failed for %s", namespace.value)
        return None


async def cache_set(
    namespace: CacheNamespace,
    *key_parts: str,
    value: str,
    project_id: str | None = None,
    ttl: int | None = None,
) -> None:
    """Store a value with TTL. Optionally index it by project for bulk invalidation.

    If project_id is provided, the key is added to a Redis SET so that
    invalidate_project_cache() can delete all related keys without SCAN.
    """
    if not settings.CACHE_ENABLED:
        return
    try:
        client = await get_redis()
        key = _build_key(namespace, *key_parts)
        expire = ttl or _TTL_MAP.get(namespace, 3600)

        pipe = client.pipeline(transaction=False)
        pipe.set(key, value, ex=expire)

        # Add to project index for targeted invalidation
        if project_id:
            idx_key = _project_pattern(namespace, project_id)
            pipe.sadd(idx_key, key)
            pipe.expire(idx_key, expire + 300)  # index lives slightly longer

        await pipe.execute()
        logger.debug("[Cache] SET %s key=%s ttl=%ds", namespace.value, key[-12:], expire)
    except Exception:
        logger.warning("[Cache] SET failed for %s", namespace.value, exc_info=True)


async def cache_set_json(
    namespace: CacheNamespace,
    *key_parts: str,
    value: dict | list,
    project_id: str | None = None,
    ttl: int | None = None,
) -> None:
    """Serialize and cache a JSON-serializable value."""
    await cache_set(
        namespace,
        *key_parts,
        value=json.dumps(value, default=str),
        project_id=project_id,
        ttl=ttl,
    )


async def invalidate_project_cache(project_id: str) -> int:
    """Delete ALL cached entries for a project across all namespaces.

    Called when documents are ingested, updated, or deleted — ensures the
    cache never serves stale context from outdated document chunks.

    Uses the project index SETs instead of SCAN for O(n) deletion where
    n = number of cached keys for that project, not total keys in Redis.

    Returns the number of keys deleted.
    """
    if not settings.CACHE_ENABLED:
        return 0
    try:
        client = await get_redis()
        total_deleted = 0

        for ns in (CacheNamespace.LLM, CacheNamespace.RETRIEVAL):
            idx_key = _project_pattern(ns, project_id)
            keys = await client.smembers(idx_key)
            if keys:
                pipe = client.pipeline(transaction=False)
                for key in keys:
                    pipe.delete(key)
                pipe.delete(idx_key)
                results = await pipe.execute()
                deleted = sum(1 for r in results[:-1] if r)
                total_deleted += deleted

        if total_deleted:
            logger.info(
                "[Cache] Invalidated %d keys for project %s",
                total_deleted, project_id[:8],
            )
        return total_deleted
    except Exception:
        logger.warning(
            "[Cache] Invalidation failed for project %s",
            project_id[:8], exc_info=True,
        )
        return 0


async def invalidate_namespace(namespace: CacheNamespace) -> int:
    """Flush all keys in a namespace using pattern-based SCAN.

    Use sparingly — only for admin operations like full cache reset.
    For project-scoped invalidation, use invalidate_project_cache() instead.
    """
    if not settings.CACHE_ENABLED:
        return 0
    try:
        client = await get_redis()
        pattern = f"{settings.CACHE_KEY_PREFIX}:{namespace.value}:*"
        deleted = 0
        async for key in client.scan_iter(match=pattern, count=100):
            await client.delete(key)
            deleted += 1
        logger.info("[Cache] Flushed %d keys in namespace %s", deleted, namespace.value)
        return deleted
    except Exception:
        logger.warning("[Cache] Namespace flush failed for %s", namespace.value, exc_info=True)
        return 0


async def get_cache_stats() -> dict:
    """Return cache statistics for the health/admin endpoint."""
    try:
        client = await get_redis()
        info = await client.info("memory", "stats", "keyspace")
        return {
            "connected": True,
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "total_keys": info.get("db0", {}).get("keys", 0) if isinstance(info.get("db0"), dict) else 0,
            "hit_rate": _calc_hit_rate(info),
            "evicted_keys": info.get("evicted_keys", 0),
        }
    except Exception:
        return {"connected": False}


def _calc_hit_rate(info: dict) -> float:
    """Calculate cache hit rate from Redis INFO stats."""
    hits = info.get("keyspace_hits", 0)
    misses = info.get("keyspace_misses", 0)
    total = hits + misses
    return round(hits / total, 4) if total > 0 else 0.0
