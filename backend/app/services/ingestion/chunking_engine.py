from __future__ import annotations

import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.services.ingestion.text_cleaner import clean_text, prepare_chunk_for_embedding

# Cache the encoding so it's only loaded once
_encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")


def create_chunker(
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> RecursiveCharacterTextSplitter:
    """Create a boundary-aware text splitter."""
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=lambda t: len(_encoding.encode(t)),
        separators=[
            "\n## ",      # Markdown H2
            "\n### ",     # Markdown H3
            "\n#### ",    # Markdown H4
            "\n\n",       # Double newline (paragraph)
            "\n",         # Single newline
            ". ",         # Sentence boundary
            " ",          # Word boundary
        ],
    )


def chunk_document(
    content: str,
    document_id: str,
    section_title: str | None = None,
    page_number: int | None = None,
    source_url: str | None = None,
    project_id: str | None = None,
    document_title: str | None = None,
) -> list[dict]:
    """Clean, chunk, and prepare text with metadata for embedding."""
    # Clean the text before chunking
    cleaned = clean_text(content)
    if not cleaned.strip():
        return []

    chunker = create_chunker()
    texts = chunker.split_text(cleaned)

    chunks = []
    for i, text in enumerate(texts):
        # Build an embedding-optimized version with contextual prefix
        embedding_text = prepare_chunk_for_embedding(
            content=text,
            section_title=section_title,
            document_title=document_title,
        )

        metadata: dict[str, str | int | float] = {
            "document_id": document_id,
            "section_title": section_title or "Unknown",
            "project_id": project_id or "",
            "chunk_index": i,
            "total_chunks": len(texts),
        }
        if page_number is not None:
            metadata["page_number"] = page_number
        if source_url is not None:
            metadata["source_url"] = source_url

        chunks.append({
            "content": text,
            "embedding_text": embedding_text,
            "chunk_index": i,
            "metadata": metadata,
        })
    return chunks
