from __future__ import annotations

import re
from pathlib import Path


def parse_markdown(file_path: str | Path) -> list[dict]:
    """Parse markdown into sections based on headings."""
    content = Path(file_path).read_text(encoding="utf-8")
    sections: list[dict] = []
    current_section: dict = {"title": "Introduction", "content": "", "level": 0}

    for line in content.split("\n"):
        heading_match = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading_match:
            if current_section["content"].strip():
                sections.append(current_section.copy())
            level = len(heading_match.group(1))
            current_section = {
                "title": heading_match.group(2).strip(),
                "content": "",
                "level": level,
            }
        else:
            current_section["content"] += line + "\n"

    if current_section["content"].strip():
        sections.append(current_section)

    result: list[dict] = []
    for s in sections:
        body = s["content"].strip()
        if not body:
            continue
        # Prepend the heading into the content so the embedding model
        # sees the topic context, not just the body text.
        heading_prefix = f"{'#' * s['level']} {s['title']}\n\n" if s["level"] > 0 else ""
        result.append({
            "content": heading_prefix + body,
            "section_title": s["title"],
            "metadata": {"source_type": "markdown", "heading_level": s["level"]},
        })
    return result
