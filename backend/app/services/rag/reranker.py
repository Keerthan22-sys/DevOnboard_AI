from __future__ import annotations

import logging

from sentence_transformers import CrossEncoder

from app.config import settings

logger = logging.getLogger(__name__)

# Singleton — loaded once, reused across requests
_reranker: CrossEncoder | None = None


def get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        logger.info("Loading cross-encoder rerank model: %s", settings.RERANK_MODEL)
        _reranker = CrossEncoder(settings.RERANK_MODEL, max_length=512)
    return _reranker


def rerank_chunks(
    query: str,
    chunks: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """Re-score chunks using a cross-encoder and return the top_k.

    The cross-encoder takes (query, passage) pairs and produces a
    relevance score with full token-level attention — much more
    accurate than cosine similarity from bi-encoders.
    """
    if not chunks:
        return []

    reranker = get_reranker()

    pairs = [[query, c["content"]] for c in chunks]
    scores = reranker.predict(pairs).tolist()

    for chunk, score in zip(chunks, scores):
        chunk["rerank_score"] = float(score)

    # Sort by rerank score descending
    chunks.sort(key=lambda c: c["rerank_score"], reverse=True)
    selected = chunks[:top_k]

    labels = [f"{c['rerank_score']:.3f}" for c in selected]
    logger.info("[Rerank] query=%r top_%d scores=[%s]", query[:80], top_k, ", ".join(labels))

    return selected
