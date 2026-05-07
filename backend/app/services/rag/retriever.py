from __future__ import annotations

import logging
import math

from app.services.cache.cache_manager import CacheNamespace, cache_get_json, cache_set_json
from app.services.rag.embeddings import get_collection, get_embedding_model
from app.services.rag.reranker import rerank_chunks

logger = logging.getLogger(__name__)


def retrieve_chunks(
    query: str,
    project_id: str,
    top_k: int = 20,
    final_k: int = 5,
    hyde_text: str | None = None,
) -> list[dict]:
    """Three-stage retrieval: multi-query recall → dedupe → cross-encoder rerank.

    Stage 1: Embed the original query AND the HyDE hypothesis (if provided),
             query ChromaDB with both, union the results.
    Stage 2: Deduplicate by chunk content.
    Stage 3: Re-score with cross-encoder → return final_k.
    """
    model = get_embedding_model()
    collection = get_collection(project_id)

    # Build embeddings for original query + optional HyDE expansion
    query_embedding = model.encode(query).tolist()
    embeddings_to_search = [query_embedding]

    if hyde_text and hyde_text != query:
        hyde_embedding = model.encode(hyde_text).tolist()
        embeddings_to_search.append(hyde_embedding)

    # Fetch candidates from each embedding
    seen_contents: set[str] = set()
    candidates: list[dict] = []

    for emb in embeddings_to_search:
        results = collection.query(
            query_embeddings=[emb],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        if not results["documents"] or not results["documents"][0]:
            continue

        for i, doc in enumerate(results["documents"][0]):
            # Deduplicate by content hash
            content_key = doc[:200]  # fast dedup on prefix
            if content_key in seen_contents:
                continue
            seen_contents.add(content_key)

            cosine_score = 1 - results["distances"][0][i]
            candidates.append({
                "content": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
                "relevance_score": cosine_score,
            })

    if not candidates:
        logger.info("[RAG] No chunks found for project=%s query=%r", project_id, query[:80])
        return []

    bi_scores = [f"{c['relevance_score']:.3f}" for c in sorted(
        candidates, key=lambda c: c["relevance_score"], reverse=True
    )[:5]]
    logger.info(
        "[RAG] Stage 1 (bi-encoder, %d queries): project=%s query=%r "
        "%d candidates, top-5 cosine=[%s]",
        len(embeddings_to_search), project_id, query[:80],
        len(candidates), ", ".join(bi_scores),
    )

    # Stage 2: Cross-encoder rerank
    reranked = rerank_chunks(query=query, chunks=candidates, top_k=final_k)

    # Normalize rerank scores to 0-1 for the API response
    for chunk in reranked:
        raw = chunk["rerank_score"]
        chunk["relevance_score"] = _sigmoid(raw)

    final_scores = [f"{c['relevance_score']:.3f}" for c in reranked]
    logger.info(
        "[RAG] Stage 2 (reranked): project=%s query=%r final scores=[%s]",
        project_id, query[:80], ", ".join(final_scores),
    )

    return reranked


async def retrieve_chunks_cached(
    query: str,
    project_id: str,
    top_k: int = 20,
    final_k: int = 5,
    hyde_text: str | None = None,
) -> list[dict]:
    """Cache-aware wrapper around retrieve_chunks.

    Cache strategy:
    - Key: hash of (query, project_id, hyde_text)
    - TTL: CACHE_TTL_RETRIEVAL (default 30 min)
    - Indexed by project_id — automatically invalidated when docs change.
    - Falls back to live retrieval if Redis is unavailable.
    """
    cache_parts = (query, project_id, str(hyde_text or ""))

    # Check cache
    cached = await cache_get_json(CacheNamespace.RETRIEVAL, *cache_parts)
    if cached is not None:
        logger.info("[RAG Cache] HIT — returning %d cached chunks for project=%s", len(cached), project_id[:8])
        return cached

    # Cache miss — run full retrieval pipeline
    chunks = retrieve_chunks(
        query=query,
        project_id=project_id,
        top_k=top_k,
        final_k=final_k,
        hyde_text=hyde_text,
    )

    # Cache the result (fire-and-forget)
    if chunks:
        await cache_set_json(
            CacheNamespace.RETRIEVAL,
            *cache_parts,
            value=chunks,
            project_id=project_id,
        )

    return chunks


def _sigmoid(x: float) -> float:
    """Map cross-encoder logits to 0-1 probability."""
    return 1.0 / (1.0 + math.exp(-x))
