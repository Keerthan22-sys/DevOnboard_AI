from __future__ import annotations

import logging
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

logger = logging.getLogger(__name__)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.credential import IntegrationCredential
from app.models.document import Document
from app.models.project import Project
from app.models.user import User
from app.schemas.document import (
    ConfluenceIngestRequest,
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadResponse,
    GithubIngestRequest,
)
from app.services.ingestion import ingest_file
from app.services.ingestion.confluence_scraper import scrape_confluence_page
from app.services.ingestion.github_indexer import clone_and_index
from app.services.rag.embeddings import delete_document_chunks
from app.utils.encryption import decrypt_value
from app.utils.file_handler import save_upload, validate_file

router = APIRouter(prefix="/api/projects/{project_id}/documents", tags=["documents"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_project_or_404(
    project_id: UUID,
    db: AsyncSession,
) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ---------------------------------------------------------------------------
# POST /upload — multipart file upload
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    project_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, db)

    try:
        validate_file(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save file to disk
    file_path, content_hash = await save_upload(file, str(project_id))

    # Create document record
    doc = Document(
        project_id=project_id,
        title=file.filename or "Untitled",
        source_type=Path(file.filename or "").suffix.lstrip(".").lower(),
        file_path=file_path,
        content_hash=content_hash,
        status="processing",
        uploaded_by=user.id,
    )
    db.add(doc)
    await db.flush()

    # Run ingestion pipeline (synchronous for MVP)
    try:
        chunk_count = await ingest_file(
            file_path=file_path,
            document_id=str(doc.id),
            project_id=str(project_id),
            document_title=doc.title,
        )
        doc.status = "ready"
        doc.chunk_count = chunk_count
    except Exception as e:
        logger.exception("Ingestion failed for document %s", doc.id)
        doc.status = "failed"
        doc.metadata_ = {"error": str(e)}

    await db.flush()
    return doc


# ---------------------------------------------------------------------------
# POST /confluence — scrape Confluence URL
# ---------------------------------------------------------------------------

@router.post("/confluence", response_model=DocumentUploadResponse, status_code=201)
async def ingest_confluence(
    project_id: UUID,
    data: ConfluenceIngestRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, db)

    # Look up stored Confluence credentials for this project
    cred_result = await db.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.project_id == project_id,
            IntegrationCredential.integration_type == "confluence",
        )
    )
    cred = cred_result.scalar_one_or_none()

    try:
        if cred:
            page = await scrape_confluence_page(
                data.url,
                api_token=decrypt_value(cred.encrypted_token),
                email=cred.email,
                base_url=cred.base_url,
            )
        else:
            page = await scrape_confluence_page(data.url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to scrape URL: {e}")

    title = data.title or page.get("title", "Confluence Page")

    # Reconstruct markdown with section headings for better RAG chunking
    md_parts = [f"# {title}\n"]
    for section in page.get("sections", []):
        heading = section.get("title", "")
        body = section.get("content", "").strip()
        if heading and heading != "Introduction":
            md_parts.append(f"## {heading}\n")
        if body:
            md_parts.append(body + "\n")
    md_content = "\n".join(md_parts) if len(md_parts) > 1 else page["content"]

    upload_dir = Path(settings.UPLOAD_DIR) / str(project_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    md_path = upload_dir / f"{title.replace(' ', '_')}.md"
    md_path.write_text(md_content, encoding="utf-8")

    doc = Document(
        project_id=project_id,
        title=title,
        source_type="confluence",
        source_url=data.url,
        file_path=str(md_path),
        status="processing",
        uploaded_by=user.id,
    )
    db.add(doc)
    await db.flush()

    try:
        chunk_count = await ingest_file(
            file_path=str(md_path),
            document_id=str(doc.id),
            project_id=str(project_id),
            source_url=data.url,
            document_title=title,
        )
        doc.status = "ready"
        doc.chunk_count = chunk_count
    except Exception as e:
        doc.status = "failed"
        doc.metadata_ = {"error": str(e)}

    await db.flush()
    return doc


# ---------------------------------------------------------------------------
# POST /github — clone and index a GitHub repo
# ---------------------------------------------------------------------------

@router.post("/github", response_model=DocumentUploadResponse, status_code=201)
async def ingest_github(
    project_id: UUID,
    data: GithubIngestRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, db)

    # Look up stored credentials for this platform
    platform = data.platform if data.platform in ("github", "gitlab") else "github"
    cred_result = await db.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.project_id == project_id,
            IntegrationCredential.integration_type == platform,
        )
    )
    cred = cred_result.scalar_one_or_none()
    token = decrypt_value(cred.encrypted_token) if cred else None

    # Clone and index the repo
    repo_dir = Path(settings.REPO_DIR) / str(project_id)
    repo_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = clone_and_index(
            data.repo_url,
            target_dir=str(repo_dir / "repo"),
            token=token,
            platform=platform,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    title = data.title or data.repo_url.rstrip("/").split("/")[-1]

    doc = Document(
        project_id=project_id,
        title=title,
        source_type=platform,
        source_url=data.repo_url,
        status="processing",
        metadata_={"file_count": result["file_count"], "structure": result["structure"]},
        uploaded_by=user.id,
    )
    db.add(doc)
    await db.flush()

    # Write each indexed file as a temp markdown and ingest
    total_chunks = 0
    upload_dir = Path(settings.UPLOAD_DIR) / str(project_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Ingest the project structure tree as a searchable document
        if result["structure"]:
            tree_content = f"# Project Structure\n\n```\n{result['structure']}\n```"
            tree_path = upload_dir / "_project_structure.md"
            tree_path.write_text(tree_content, encoding="utf-8")
            chunk_count = await ingest_file(
                file_path=str(tree_path),
                document_id=str(doc.id),
                project_id=str(project_id),
                source_url=data.repo_url,
                document_title=f"{title} - Project Structure",
            )
            total_chunks += chunk_count

        for indexed_file in result["files"]:
            tmp_path = upload_dir / indexed_file["path"].replace("/", "_")
            tmp_path.write_text(indexed_file["content"], encoding="utf-8")

            suffix = Path(indexed_file["path"]).suffix.lower()
            if suffix not in (".pdf", ".md", ".markdown", ".txt", ".text"):
                # Treat code and config files as plain text
                tmp_txt = tmp_path.with_suffix(".txt")
                tmp_path.rename(tmp_txt)
                tmp_path = tmp_txt

            chunk_count = await ingest_file(
                file_path=str(tmp_path),
                document_id=str(doc.id),
                project_id=str(project_id),
                source_url=data.repo_url,
                document_title=f"{title} - {indexed_file['path']}",
            )
            total_chunks += chunk_count

        doc.status = "ready"
        doc.chunk_count = total_chunks
    except Exception as e:
        doc.status = "failed"
        doc.metadata_ = {**doc.metadata_, "error": str(e)}

    await db.flush()
    return doc


# ---------------------------------------------------------------------------
# GET / — list documents for a project
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[DocumentListResponse])
async def list_documents(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, db)

    result = await db.execute(
        select(Document)
        .where(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# GET /:doc_id — get single document details
# ---------------------------------------------------------------------------

@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    project_id: UUID,
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, db)

    result = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.project_id == project_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


# ---------------------------------------------------------------------------
# DELETE /:doc_id — remove a document
# ---------------------------------------------------------------------------

@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    project_id: UUID,
    doc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await _get_project_or_404(project_id, db)

    result = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.project_id == project_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove chunks from ChromaDB BEFORE deleting the DB record
    delete_document_chunks(
        project_id=str(project_id),
        document_id=str(doc_id),
    )

    # Remove file from disk if it exists
    if doc.file_path:
        file_path = Path(doc.file_path)
        if file_path.exists():
            file_path.unlink()

    await db.delete(doc)
