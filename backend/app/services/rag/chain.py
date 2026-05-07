from __future__ import annotations

from app.config import settings
from app.services.llm.ollama_client import generate_response
from app.services.rag.hyde import generate_hypothetical_answer
from app.services.rag.prompts import SYSTEM_PROMPT, build_qa_prompt
from app.services.rag.retriever import retrieve_chunks_cached


async def ask_question(
    question: str,
    project_id: str,
) -> dict:
    """Full RAG pipeline: (optional HyDE) → retrieve → rerank → build prompt → generate → cite."""

    # Step 1: Generate hypothetical answer for better retrieval (skippable)
    hyde_text: str | None = None
    if settings.HYDE_ENABLED:
        hyde_text = await generate_hypothetical_answer(question)

    # Step 2: Retrieve relevant chunks (multi-query + rerank) — Redis-cached
    chunks = await retrieve_chunks_cached(
        query=question,
        project_id=project_id,
        hyde_text=hyde_text,
    )

    if not chunks:
        return {
            "answer": (
                "I don't have any documentation indexed for this project yet. "
                "Please upload some documents first."
            ),
            "sources": [],
            "chunks_used": 0,
        }

    # Step 3: Build prompt with context
    prompt = build_qa_prompt(question=question, context_chunks=chunks)

    # Step 4: Generate response via LLM — Redis-cached by project
    answer = await generate_response(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        project_id=project_id,
    )

    # Step 5: Extract source citations
    sources = []
    seen: set[str] = set()
    for chunk in chunks:
        meta = chunk["metadata"]
        doc_id = meta.get("document_id", "")
        if doc_id not in seen:
            seen.add(doc_id)
            sources.append({
                "document_id": doc_id,
                "section_title": meta.get("section_title", "Unknown"),
                "source_url": meta.get("source_url"),
                "page_number": meta.get("page_number"),
                "relevance_score": round(chunk.get("relevance_score", 0), 3),
            })

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(chunks),
    }
