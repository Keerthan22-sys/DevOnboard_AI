from __future__ import annotations

import logging

import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis

from app.config import settings

logger = logging.getLogger(__name__)

# Module-level connection pool — shared across the entire application
_pool: ConnectionPool | None = None
_client: Redis | None = None


async def get_redis_pool() -> ConnectionPool:
    """Create or return the shared Redis connection pool.

    Uses hiredis parser for C-level performance when available.
    Pool is sized for async FastAPI workloads (max 20 connections).
    """
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            password=settings.REDIS_PASSWORD or None,
            max_connections=20,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        logger.info("[Redis] Connection pool created: %s", settings.REDIS_URL)
    return _pool


async def get_redis() -> Redis:
    """Return the shared async Redis client.

    The client is a thin wrapper around the connection pool.
    Safe to call from any coroutine — pool handles concurrency.
    """
    global _client
    if _client is None:
        pool = await get_redis_pool()
        _client = Redis(connection_pool=pool)
    return _client


async def check_redis_health() -> bool:
    """Ping Redis and return True if reachable."""
    try:
        client = await get_redis()
        return await client.ping()
    except Exception:
        logger.warning("[Redis] Health check failed", exc_info=True)
        return False


async def close_redis() -> None:
    """Gracefully close the Redis connection pool.

    Called during FastAPI shutdown to release all connections.
    """
    global _client, _pool
    if _client is not None:
        await _client.aclose()
        _client = None
    if _pool is not None:
        await _pool.aclose()
        _pool = None
    logger.info("[Redis] Connection pool closed")
