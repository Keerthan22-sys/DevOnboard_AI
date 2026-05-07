"""Quick RAG pipeline verification — runs 5 demo questions and checks responses."""
from __future__ import annotations

import asyncio
import sys
import time

import httpx

BASE_URL = "http://localhost:8000"

DEMO_QUESTIONS = [
    "What is the tech stack used in this project and how are the services connected?",
    "How do I set up the local development environment for this project?",
    "Explain the database schema and the key relationships between tables.",
    "How does the authentication and authorization flow work?",
    "Where is the search functionality implemented in the codebase?",
]


async def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python test_rag.py <token> <project_id>")
        print("  Run seed_data.py or demo_prep.py first to get these values.")
        sys.exit(1)

    token = sys.argv[1]
    project_id = sys.argv[2]
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        passed = 0
        for i, question in enumerate(DEMO_QUESTIONS, 1):
            start = time.perf_counter()
            res = await client.post(
                f"/api/projects/{project_id}/chat",
                json={"question": question},
                headers=headers,
            )
            elapsed = time.perf_counter() - start

            if res.status_code != 200:
                print(f"[FAIL] Q{i}: HTTP {res.status_code}")
                continue

            data = res.json()["data"]
            answer = data["answer"]
            sources = data["sources"]
            chunks = data["chunks_used"]

            has_answer = len(answer) > 50
            has_sources = len(sources) > 0
            under_10s = elapsed < 10.0
            ok = has_answer and has_sources

            status = "PASS" if ok else "FAIL"
            timing = "OK" if under_10s else "SLOW"

            print(f"[{status}] Q{i} ({elapsed:.1f}s {timing}) — "
                  f"{len(answer)} chars, {len(sources)} sources, {chunks} chunks")

            if ok:
                passed += 1

        print(f"\n{passed}/{len(DEMO_QUESTIONS)} questions passed")
        sys.exit(0 if passed == len(DEMO_QUESTIONS) else 1)


if __name__ == "__main__":
    asyncio.run(main())
