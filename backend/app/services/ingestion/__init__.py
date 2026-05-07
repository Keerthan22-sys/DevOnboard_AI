from __future__ import annotations

from pathlib import Path

from app.services.ingestion.chunking_engine import chunk_document
from app.services.ingestion.markdown_parser import parse_markdown
from app.services.ingestion.pdf_parser import parse_pdf
from app.services.rag.embeddings import embed_and_store


async def ingest_file(
    file_path: str,
    document_id: str,
    project_id: str,
    source_url: str | None = None,
    document_title: str | None = None,
) -> int:
    """Parse, chunk, embed, and store a document. Returns chunk count."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if not document_title:
        document_title = path.stem

    # Step 1: Parse based on file type
    if suffix == ".pdf":
        sections = parse_pdf(file_path)
    elif suffix in (".md", ".markdown"):
        sections = parse_markdown(file_path)
    elif suffix in (".txt", ".text"):
        content = path.read_text(encoding="utf-8", errors="ignore")
        sections = [{"content": content, "section_title": path.stem, "metadata": {"source_type": "text"}}]
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    # Step 2: Chunk all sections
    all_chunks: list[dict] = []
    for section in sections:
        chunks = chunk_document(
            content=section["content"],
            document_id=document_id,
            section_title=section.get("section_title"),
            page_number=section.get("page_number"),
            source_url=source_url,
            project_id=project_id,
            document_title=document_title,
        )
        all_chunks.extend(chunks)

    if not all_chunks:
        return 0

    # Step 3: Embed and store in ChromaDB
    embed_and_store(chunks=all_chunks, project_id=project_id)

    return len(all_chunks)
