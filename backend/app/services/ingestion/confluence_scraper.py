from __future__ import annotations

import base64
import re
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


async def scrape_confluence_page(
    url: str,
    api_token: str | None = None,
    email: str | None = None,
    base_url: str | None = None,
    depth: int = 1,
) -> dict:
    """Scrape a Confluence page.

    If api_token + email are provided, uses the REST API (supports private pages).
    Otherwise falls back to unauthenticated HTML scraping (public pages only).
    """
    if api_token and email:
        return await _scrape_via_api(url, api_token, email, base_url, depth)
    return await _scrape_via_html(url)


# ---------------------------------------------------------------------------
# Authenticated path — Confluence REST API
# ---------------------------------------------------------------------------

def _parse_confluence_url(url: str, base_url: str | None = None) -> tuple[str, str]:
    """Extract (base_url, page_id) from a Confluence URL.

    Supported formats:
      Cloud:  https://x.atlassian.net/wiki/spaces/SPACE/pages/12345/Title
      Server: https://confluence.example.com/pages/viewpage.action?pageId=12345
    """
    parsed = urlparse(url)

    # Cloud URL: /wiki/spaces/SPACE/pages/{page_id}/...
    cloud_match = re.search(r"/wiki/spaces/[^/]+/pages/(\d+)", parsed.path)
    if cloud_match:
        resolved_base = base_url or f"{parsed.scheme}://{parsed.netloc}/wiki"
        return resolved_base, cloud_match.group(1)

    # Server URL with pageId query param
    page_id_match = re.search(r"pageId=(\d+)", url)
    if page_id_match:
        resolved_base = base_url or f"{parsed.scheme}://{parsed.netloc}"
        return resolved_base, page_id_match.group(1)

    # Server URL: /pages/{page_id}/...  (numeric path segment)
    path_match = re.search(r"/pages/(\d+)", parsed.path)
    if path_match:
        resolved_base = base_url or f"{parsed.scheme}://{parsed.netloc}"
        return resolved_base, path_match.group(1)

    raise ValueError(
        f"Could not extract page ID from URL: {url}. "
        "Provide a URL containing a numeric page ID."
    )


async def _scrape_via_api(
    url: str,
    api_token: str,
    email: str,
    base_url: str | None,
    depth: int,
) -> dict:
    """Fetch page content via Confluence REST API with Basic Auth."""
    resolved_base, page_id = _parse_confluence_url(url, base_url)

    auth_header = base64.b64encode(f"{email}:{api_token}".encode()).decode()
    headers = {"Authorization": f"Basic {auth_header}", "Accept": "application/json"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{resolved_base}/rest/api/content/{page_id}",
            params={"expand": "body.storage,children.page,metadata.labels"},
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    title = data.get("title", "Confluence Page")
    storage_html = data.get("body", {}).get("storage", {}).get("value", "")

    soup = BeautifulSoup(storage_html, "html.parser")
    sections = _extract_sections(soup)
    text_content = soup.get_text(separator="\n", strip=True)

    return {
        "title": title,
        "content": text_content,
        "sections": sections,
        "url": url,
        "metadata": {"source_type": "confluence", "source_url": url},
    }


# ---------------------------------------------------------------------------
# Unauthenticated path — HTML scraping (public pages only)
# ---------------------------------------------------------------------------

async def _scrape_via_html(url: str) -> dict:
    """Scrape a publicly accessible Confluence page via HTML."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract main content — Confluence uses specific div IDs
    content_div = (
        soup.find("div", {"id": "main-content"})
        or soup.find("div", {"class": "wiki-content"})
        or soup.find("article")
        or soup.find("main")
    )

    if not content_div:
        content_div = soup.find("body")

    # Remove navigation, sidebars, scripts
    for tag in content_div.find_all(["nav", "script", "style", "footer", "header"]):
        tag.decompose()

    # Extract title
    title = ""
    title_tag = soup.find("title") or soup.find("h1")
    if title_tag:
        title = title_tag.get_text(strip=True)

    # Extract sections based on headings
    sections = _extract_sections(content_div)

    # Extract text content
    text_content = content_div.get_text(separator="\n", strip=True)

    return {
        "title": title,
        "content": text_content,
        "sections": sections,
        "url": url,
        "metadata": {"source_type": "confluence", "source_url": url},
    }


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _extract_sections(element: BeautifulSoup) -> list[dict]:
    """Extract sections divided by heading tags."""
    sections: list[dict] = []
    current: dict = {"title": "Introduction", "content": ""}

    for child in element.children:
        if hasattr(child, "name") and child.name in ["h1", "h2", "h3", "h4"]:
            if current["content"].strip():
                sections.append(current.copy())
            current = {"title": child.get_text(strip=True), "content": ""}
        elif hasattr(child, "get_text"):
            current["content"] += child.get_text(separator="\n", strip=True) + "\n"

    if current["content"].strip():
        sections.append(current)

    return sections
