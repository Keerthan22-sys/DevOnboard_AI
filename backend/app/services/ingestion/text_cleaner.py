from __future__ import annotations

import re


def clean_text(text: str) -> str:
    """Normalize and clean text before embedding.

    Removes noise that degrades embedding quality: excessive whitespace,
    HTML artifacts, control characters, redundant separators, and
    long base64/hex blobs.
    """
    # Strip residual HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove HTML entities
    text = re.sub(r"&[a-zA-Z]+;", " ", text)

    # Remove very long hex/base64 blobs (common in scraped pages)
    text = re.sub(r"[A-Za-z0-9+/=]{80,}", " ", text)

    # Collapse repeated punctuation/separators (--- === *** etc.)
    text = re.sub(r"[-=*_~]{3,}", " ", text)

    # Normalize whitespace: tabs, multiple spaces, multiple newlines
    text = re.sub(r"\t", " ", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


def prepare_chunk_for_embedding(
    content: str,
    section_title: str | None = None,
    document_title: str | None = None,
) -> str:
    """Build an embedding-optimized string from a chunk.

    Prepends contextual prefix so the embedding model understands
    *what* the chunk is about, not just the raw body text.
    """
    parts: list[str] = []
    if document_title:
        parts.append(f"Document: {document_title}")
    if section_title and section_title != "Unknown":
        parts.append(f"Section: {section_title}")
    parts.append(content)
    return "\n".join(parts)
