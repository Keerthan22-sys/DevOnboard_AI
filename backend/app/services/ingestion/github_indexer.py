from __future__ import annotations

import tempfile
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from git import Repo

INDEXABLE_EXTENSIONS = {
    ".md", ".txt", ".rst", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".go", ".rs", ".yml", ".yaml", ".json", ".toml",
    ".dockerfile", ".sh", ".sql",
}

PRIORITY_FILES = [
    "README.md", "CONTRIBUTING.md", "CHANGELOG.md",
    "docker-compose.yml", "Dockerfile", ".env.example",
    "package.json", "requirements.txt", "pyproject.toml",
    "pom.xml", "go.mod", "Cargo.toml",
]

PRIORITY_DIRS = ["docs", "doc", "documentation", "wiki", ".github"]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".next", "dist", "build"}


def _normalize_repo_url(repo_url: str, platform: str) -> tuple[str, str | None]:
    """Convert a web UI URL into a proper git clone URL.

    Returns (clone_url, branch_or_none).

    Examples:
      GitLab web URL:
        https://gitlab.com/org/repo/-/tree/feature/branch?ref_type=heads
        → (https://gitlab.com/org/repo.git, feature/branch)
      GitHub web URL:
        https://github.com/org/repo/tree/main
        → (https://github.com/org/repo.git, main)
      Already a clone URL:
        https://github.com/org/repo.git → unchanged
    """
    parsed = urlparse(repo_url)
    path = parsed.path.rstrip("/")
    branch: str | None = None

    if platform == "gitlab" and "/-/" in path:
        # GitLab web URL: /org/repo/-/tree/branch-name
        repo_path, _, rest = path.partition("/-/")
        if rest.startswith("tree/"):
            branch = rest[len("tree/"):]
        path = repo_path

    elif platform == "github" and "/tree/" in path:
        # GitHub web URL: /org/repo/tree/branch-name
        repo_path, _, branch = path.partition("/tree/")
        path = repo_path

    # Ensure .git suffix for clean cloning
    if not path.endswith(".git"):
        path = path + ".git"

    clean_url = urlunparse(parsed._replace(path=path, query="", fragment=""))
    return clean_url, branch


def _build_authenticated_url(repo_url: str, token: str, platform: str) -> str:
    """Insert credentials into the clone URL without logging them."""
    parsed = urlparse(repo_url)
    if platform == "gitlab":
        netloc = f"oauth2:{token}@{parsed.hostname}"
    else:
        netloc = f"{token}@{parsed.hostname}"
    if parsed.port:
        netloc += f":{parsed.port}"
    return urlunparse(parsed._replace(netloc=netloc))


def clone_and_index(
    repo_url: str,
    target_dir: str | None = None,
    token: str | None = None,
    platform: str = "github",
) -> dict:
    """Clone a git repo and extract indexable content."""
    clone_dir = target_dir or tempfile.mkdtemp(prefix="devonboard_repo_")

    # Normalize web UI URLs to proper clone URLs
    normalized_url, branch = _normalize_repo_url(repo_url, platform)

    clone_url = normalized_url
    if token:
        clone_url = _build_authenticated_url(normalized_url, token, platform)

    clone_kwargs: dict = {"depth": 1}
    if branch:
        clone_kwargs["branch"] = branch

    try:
        Repo.clone_from(clone_url, clone_dir, **clone_kwargs)
    except Exception as e:
        # Never leak the authenticated URL in error messages
        raise RuntimeError(f"Failed to clone {repo_url}: {e}")

    repo_path = Path(clone_dir)
    indexed_files: list[dict] = []
    seen_paths: set[str] = set()

    source_type = platform  # "github" or "gitlab"

    # Index priority files first
    for filename in PRIORITY_FILES:
        fpath = repo_path / filename
        if fpath.exists():
            rel = str(fpath.relative_to(repo_path))
            seen_paths.add(rel)
            indexed_files.append({
                "path": rel,
                "content": fpath.read_text(encoding="utf-8", errors="ignore"),
                "priority": "high",
                "metadata": {"source_type": source_type, "file_type": fpath.suffix},
            })

    # Index priority directories
    for dirname in PRIORITY_DIRS:
        dirpath = repo_path / dirname
        if dirpath.is_dir():
            for fpath in dirpath.rglob("*"):
                if fpath.is_file() and fpath.suffix in INDEXABLE_EXTENSIONS:
                    rel = str(fpath.relative_to(repo_path))
                    if rel in seen_paths:
                        continue
                    try:
                        content = fpath.read_text(encoding="utf-8", errors="ignore")
                        if len(content) < 100_000:  # Skip very large files
                            seen_paths.add(rel)
                            indexed_files.append({
                                "path": rel,
                                "content": content,
                                "priority": "medium",
                                "metadata": {"source_type": source_type, "file_type": fpath.suffix},
                            })
                    except Exception:
                        continue

    # Index remaining indexable files in the repo
    for fpath in repo_path.rglob("*"):
        if not fpath.is_file():
            continue
        if fpath.suffix not in INDEXABLE_EXTENSIONS:
            continue
        # Skip already-indexed and files inside skip dirs
        rel = str(fpath.relative_to(repo_path))
        if rel in seen_paths:
            continue
        if any(part in SKIP_DIRS for part in fpath.relative_to(repo_path).parts):
            continue
        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
            if len(content) < 100_000:
                seen_paths.add(rel)
                indexed_files.append({
                    "path": rel,
                    "content": content,
                    "priority": "low",
                    "metadata": {"source_type": source_type, "file_type": fpath.suffix},
                })
        except Exception:
            continue

    # Generate project structure tree
    structure = _generate_tree(repo_path, max_depth=3)

    return {
        "files": indexed_files,
        "structure": structure,
        "repo_url": repo_url,
        "file_count": len(indexed_files),
    }


def _generate_tree(path: Path, prefix: str = "", max_depth: int = 3, depth: int = 0) -> str:
    """Generate a text-based directory tree."""
    if depth >= max_depth:
        return ""

    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv", ".next", "dist", "build"}
    lines: list[str] = []
    entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))

    for entry in entries:
        if entry.name in skip_dirs or entry.name.startswith("."):
            continue
        if entry.is_dir():
            lines.append(f"{prefix}{entry.name}/")
            lines.append(_generate_tree(entry, prefix + "  ", max_depth, depth + 1))
        else:
            lines.append(f"{prefix}{entry.name}")
    return "\n".join(filter(None, lines))
