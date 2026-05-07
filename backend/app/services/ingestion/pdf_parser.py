from __future__ import annotations

from pathlib import Path

import pdfplumber


def parse_pdf(file_path: str | Path) -> list[dict]:
    """Extract text from PDF with page-level metadata."""
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({
                    "content": text,
                    "page_number": i + 1,
                    "metadata": {
                        "source_type": "pdf",
                        "page": i + 1,
                        "total_pages": len(pdf.pages),
                    },
                })
    return pages
