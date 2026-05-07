from __future__ import annotations

import asyncio
import hashlib
import logging

import chromadb
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.services.cache.cache_manager import invalidate_project_cache

logger = logging.getLogger(__name__)

# Singleton model loader — loads once, reused across requests
_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def get_chroma_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
        settings=chromadb.Settings(anonymized_telemetry=False),
    )


def get_collection(project_id: str) -> chromadb.Collection:
    """Get or create a ChromaDB collection for a project."""
    client = get_chroma_client()
    collection_name = f"project_{project_id.replace('-', '_')}"
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def embed_and_store(
    chunks: list[dict],
    project_id: str,
) -> list[str]:
    """Embed chunks and store in ChromaDB. Returns list of embedding IDs.

    Uses 'embedding_text' (contextual prefix + content) for encoding
    but stores 'content' (clean text) as the ChromaDB document so the
    LLM prompt gets clean context without the synthetic prefix.

    Deduplicates by content hash to avoid re-indexing identical passages.
    """
    if not chunks:
        return []

    model = get_embedding_model()
    collection = get_collection(project_id)

    # Use embedding_text if available, otherwise fall back to content
    texts_for_embedding = [
        c.get("embedding_text", c["content"]) for c in chunks
    ]
    texts_for_storage = [c["content"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    # Generate deterministic IDs from content hash for dedup
    ids: list[str] = []
    for chunk in chunks:
        content_hash = hashlib.sha256(chunk["content"].encode()).hexdigest()[:16]
        doc_id = chunk["metadata"].get("document_id", "")[:8]
        ids.append(f"{doc_id}_{content_hash}")

    # Filter out chunks that already exist in the collection
    try:
        existing = collection.get(ids=ids)
        existing_ids = set(existing["ids"]) if existing["ids"] else set()
    except Exception:
        existing_ids = set()

    new_indices = [i for i, cid in enumerate(ids) if cid not in existing_ids]
    if not new_indices:
        logger.info("[Embed] All %d chunks already exist, skipping", len(chunks))
        return ids

    new_texts = [texts_for_embedding[i] for i in new_indices]
    new_docs = [texts_for_storage[i] for i in new_indices]
    new_meta = [metadatas[i] for i in new_indices]
    new_ids = [ids[i] for i in new_indices]

    embeddings = model.encode(new_texts, show_progress_bar=False).tolist()

    collection.add(
        ids=new_ids,
        embeddings=embeddings,
        documents=new_docs,
        metadatas=new_meta,
    )

    logger.info(
        "[Embed] Stored %d new chunks (%d skipped as dupes) for project %s",
        len(new_ids), len(chunks) - len(new_ids), project_id[:8],
    )

    # Invalidate cached RAG/LLM responses — new docs mean stale answers
    asyncio.get_event_loop().create_task(invalidate_project_cache(project_id))

    return ids


def delete_document_chunks(project_id: str, document_id: str) -> int:
    """Remove all chunks for a document from ChromaDB. Returns count deleted."""
    collection = get_collection(project_id)

    # Fetch IDs of all chunks belonging to this document
    results = collection.get(
        where={"document_id": document_id},
        include=[],
    )

    if not results["ids"]:
        logger.info("[Embed] No chunks found in ChromaDB for document %s", document_id[:8])
        return 0

    collection.delete(ids=results["ids"])
    logger.info(
        "[Embed] Deleted %d chunks from ChromaDB for document %s (project %s)",
        len(results["ids"]), document_id[:8], project_id[:8],
    )

    # Invalidate cached answers that referenced these chunks
    asyncio.get_event_loop().create_task(invalidate_project_cache(project_id))

    return len(results["ids"])


def delete_project_collection(project_id: str) -> bool:
    """Delete the entire ChromaDB collection for a project.

    Called when a project is deleted — removes ALL vectors at once
    instead of document-by-document.
    """
    client = get_chroma_client()
    collection_name = f"project_{project_id.replace('-', '_')}"

    try:
        client.delete_collection(name=collection_name)
        logger.info("[Embed] Deleted ChromaDB collection %s", collection_name)
        asyncio.get_event_loop().create_task(invalidate_project_cache(project_id))
        return True
    except ValueError:
        # Collection doesn't exist — nothing to delete
        logger.info("[Embed] ChromaDB collection %s not found, skipping", collection_name)
        return False
