"""Seed the database with demo data for the presentation."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8000"


async def seed() -> None:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=120.0) as client:
        # 1. Register admin user
        print("Registering demo user...")
        res = await client.post("/api/auth/register", json={
            "email": "keerthan@mhp.com",
            "name": "Keerthan",
            "password": "demo2026",
        })
        if res.status_code == 409:
            # User already exists — log in instead
            print("  User already exists, logging in...")
            res = await client.post("/api/auth/login", json={
                "email": "keerthan@mhp.com",
                "password": "demo2026",
            })
        if res.status_code not in (200, 201):
            print(f"  FAILED: {res.status_code} — {res.text}")
            sys.exit(1)

        data = res.json()
        token = data["access_token"]
        user_name = data["user"]["name"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"  Authenticated as {user_name}")

        # 2. Create demo project
        print("Creating demo project...")
        res = await client.post("/api/projects", json={
            "name": "Think Tank Platform",
            "description": "MHP's internal knowledge management platform",
        }, headers=headers)
        if res.status_code != 201:
            print(f"  FAILED: {res.status_code} — {res.text}")
            sys.exit(1)

        project_id = res.json()["id"]
        print(f"  Project created: {project_id}")

        # 3. Upload sample documents
        sample_dir = Path(__file__).parent / "sample_docs"
        if not sample_dir.exists():
            print(f"  WARNING: {sample_dir} not found — skipping document upload")
            return

        md_files = sorted(sample_dir.glob("*.md"))
        print(f"Uploading {len(md_files)} sample documents...")

        for md_file in md_files:
            content = md_file.read_bytes()
            files = {"file": (md_file.name, content, "text/markdown")}
            res = await client.post(
                f"/api/projects/{project_id}/documents/upload",
                files=files,
                headers=headers,
            )
            status = "OK" if res.status_code == 201 else f"FAILED ({res.status_code})"
            chunk_info = ""
            if res.status_code == 201:
                doc_data = res.json()
                chunk_info = f" — {doc_data.get('chunk_count', '?')} chunks"
            print(f"  {md_file.name}: {status}{chunk_info}")

        print()
        print("=" * 50)
        print("Seed data complete!")
        print(f"  Project ID: {project_id}")
        print(f"  Token: {token}")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
