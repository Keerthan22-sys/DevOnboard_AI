"""
Full demo preparation script for DevOnboard AI.

Steps:
1. Register demo user (keerthan@mhp.com)
2. Create "Think Tank Platform" project
3. Upload sample markdown documents
4. Run 5 demo questions from PRD Section 8
5. Report results with timing
"""
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8000"

DEMO_QUESTIONS = [
    "What is the tech stack used in this project and how are the services connected?",
    "How do I set up the local development environment for this project?",
    "Explain the database schema and the key relationships between tables.",
    "How does the authentication and authorization flow work?",
    "Where is the search functionality implemented in the codebase?",
]


async def check_health(client: httpx.AsyncClient) -> bool:
    """Verify the backend is running."""
    try:
        res = await client.get("/api/health")
        return res.status_code == 200
    except httpx.ConnectError:
        return False


async def register_or_login(client: httpx.AsyncClient) -> tuple[str, str]:
    """Register the demo user or log in if already exists. Returns (token, user_name)."""
    res = await client.post("/api/auth/register", json={
        "email": "keerthan@mhp.com",
        "name": "Keerthan",
        "password": "demo2026",
    })
    if res.status_code == 409:
        res = await client.post("/api/auth/login", json={
            "email": "keerthan@mhp.com",
            "password": "demo2026",
        })
    if res.status_code not in (200, 201):
        print(f"AUTH FAILED: {res.status_code} — {res.text}")
        sys.exit(1)

    data = res.json()
    return data["access_token"], data["user"]["name"]


async def create_project(
    client: httpx.AsyncClient,
    headers: dict[str, str],
) -> str:
    """Create the demo project. Returns project_id."""
    # Check if project already exists
    res = await client.get("/api/projects", headers=headers)
    if res.status_code == 200:
        projects = res.json().get("data", [])
        for p in projects:
            if p["name"] == "Think Tank Platform":
                print(f"  Project already exists: {p['id']}")
                return p["id"]

    res = await client.post("/api/projects", json={
        "name": "Think Tank Platform",
        "description": "MHP's internal knowledge management platform",
    }, headers=headers)
    if res.status_code != 201:
        print(f"PROJECT CREATE FAILED: {res.status_code} — {res.text}")
        sys.exit(1)

    project_id = res.json()["id"]
    return project_id


async def upload_documents(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    project_id: str,
) -> int:
    """Upload sample .md files. Returns count of successfully uploaded docs."""
    sample_dir = Path(__file__).parent / "sample_docs"
    if not sample_dir.exists():
        print("  ERROR: sample_docs/ directory not found")
        return 0

    # Check if documents already uploaded
    res = await client.get(
        f"/api/projects/{project_id}/documents/",
        headers=headers,
    )
    if res.status_code == 200:
        existing = res.json()
        if len(existing) > 0:
            print(f"  {len(existing)} documents already uploaded — skipping")
            return len(existing)

    md_files = sorted(sample_dir.glob("*.md"))
    uploaded = 0

    for md_file in md_files:
        content = md_file.read_bytes()
        files = {"file": (md_file.name, content, "text/markdown")}
        res = await client.post(
            f"/api/projects/{project_id}/documents/upload",
            files=files,
            headers=headers,
        )
        if res.status_code == 201:
            doc_data = res.json()
            chunks = doc_data.get("chunk_count", "?")
            print(f"  ✓ {md_file.name} — {chunks} chunks")
            uploaded += 1
        else:
            print(f"  ✗ {md_file.name} — {res.status_code}: {res.text[:100]}")

    return uploaded


async def run_demo_questions(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    project_id: str,
) -> list[dict]:
    """Run the 5 demo questions and collect results."""
    results = []
    session_id = None

    for i, question in enumerate(DEMO_QUESTIONS, 1):
        print(f"\n{'─' * 60}")
        print(f"Q{i}: {question}")
        print("─" * 60)

        payload: dict = {"question": question}
        if session_id:
            payload["session_id"] = session_id

        start = time.perf_counter()
        res = await client.post(
            f"/api/projects/{project_id}/chat",
            json=payload,
            headers=headers,
        )
        elapsed = time.perf_counter() - start

        if res.status_code != 200:
            print(f"  FAILED: {res.status_code} — {res.text[:200]}")
            results.append({
                "question": question,
                "status": "FAILED",
                "error": res.text[:200],
                "latency_s": round(elapsed, 2),
            })
            continue

        data = res.json()["data"]
        answer = data["answer"]
        sources = data["sources"]
        session_id = data["session_id"]
        chunks_used = data["chunks_used"]

        # Print answer (truncated for readability)
        print(f"\nAnswer ({elapsed:.1f}s, {chunks_used} chunks):")
        lines = answer.split("\n")
        for line in lines[:20]:
            print(f"  {line}")
        if len(lines) > 20:
            print(f"  ... ({len(lines) - 20} more lines)")

        # Print sources
        if sources:
            print(f"\nSources ({len(sources)}):")
            for s in sources:
                score = f"{s['relevance_score']:.2f}" if s.get("relevance_score") else "?"
                print(f"  - {s['section_title']} (score: {score})")

        results.append({
            "question": question,
            "status": "OK",
            "latency_s": round(elapsed, 2),
            "chunks_used": chunks_used,
            "source_count": len(sources),
            "answer_length": len(answer),
        })

    return results


async def main() -> None:
    print("=" * 60)
    print("DevOnboard AI — Demo Preparation")
    print("=" * 60)

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        # Step 0: Health check
        print("\n[1/5] Checking backend health...")
        if not await check_health(client):
            print("  ERROR: Backend not reachable at", BASE_URL)
            print("  Run: docker compose up")
            sys.exit(1)
        print("  Backend is healthy")

        # Step 1: Register/login
        print("\n[2/5] Authenticating demo user...")
        token, user_name = await register_or_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        print(f"  Logged in as {user_name}")

        # Step 2: Create project
        print("\n[3/5] Creating demo project...")
        project_id = await create_project(client, headers)
        print(f"  Project ID: {project_id}")

        # Step 3: Upload documents
        print("\n[4/5] Uploading sample documents...")
        doc_count = await upload_documents(client, headers, project_id)
        print(f"  Total documents: {doc_count}")

        # Step 4: Run demo questions
        print("\n[5/5] Running demo questions...")
        results = await run_demo_questions(client, headers, project_id)

        # Summary
        print("\n" + "=" * 60)
        print("DEMO PREP SUMMARY")
        print("=" * 60)
        print(f"  User:      keerthan@mhp.com")
        print(f"  Project:   Think Tank Platform ({project_id})")
        print(f"  Documents: {doc_count}")
        print()

        all_ok = True
        for r in results:
            status = r["status"]
            latency = r["latency_s"]
            icon = "PASS" if status == "OK" and latency < 10 else "SLOW" if status == "OK" else "FAIL"
            q_short = r["question"][:55] + "..." if len(r["question"]) > 55 else r["question"]
            extras = ""
            if status == "OK":
                extras = f" | {r['source_count']} sources, {r['chunks_used']} chunks"
            print(f"  [{icon}] {latency:5.1f}s | {q_short}{extras}")
            if icon == "FAIL":
                all_ok = False

        print()
        if all_ok:
            print("All demo questions passed! Ready for presentation.")
        else:
            print("Some questions failed — check output above.")

        print(f"\nToken for manual testing:\n  {token}")


if __name__ == "__main__":
    asyncio.run(main())
