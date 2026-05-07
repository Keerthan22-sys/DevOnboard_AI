from __future__ import annotations

import shutil
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.chat import AuditLog, ChatSession
from app.models.document import Document
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.rag.embeddings import delete_project_collection

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectResponse:
    project = Project(
        name=data.name,
        description=data.description,
        created_by=user.id,
    )
    db.add(project)
    await db.flush()

    member = ProjectMember(
        project_id=project.id,
        user_id=user.id,
        role="admin",
    )
    db.add(member)
    await db.flush()

    return ProjectResponse.model_validate(project)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectListResponse:
    result = await db.execute(
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == user.id)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return ProjectListResponse(
        data=[ProjectResponse.model_validate(p) for p in projects],
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectResponse:
    project = await _get_user_project(db, project_id, user.id)
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectResponse:
    project = await _get_user_project(db, project_id, user.id, require_admin=True)

    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description

    await db.flush()
    await db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    project = await _get_user_project(db, project_id, user.id, require_admin=True)

    # 1. Delete ChromaDB collection (all vectors for this project)
    delete_project_collection(str(project_id))

    # 2. Delete uploaded files from disk
    upload_dir = Path(settings.UPLOAD_DIR) / str(project_id)
    if upload_dir.exists():
        shutil.rmtree(upload_dir)

    # 3. Delete cloned repos from disk
    repo_dir = Path(settings.REPO_DIR) / str(project_id)
    if repo_dir.exists():
        shutil.rmtree(repo_dir)

    # 4. Delete all child rows before the project itself.
    # Order matters: chat_messages reference chat_sessions, so delete sessions
    # first (CASCADE handles messages if the DB constraint is correct, but
    # we flush between groups to force SQLAlchemy to emit DELETEs in order).
    for model in (ChatSession, AuditLog, Document, ProjectMember):
        rows = await db.execute(
            select(model).where(model.project_id == project.id)
        )
        for row in rows.scalars().all():
            await db.delete(row)
    await db.flush()

    await db.delete(project)
    await db.flush()
    return {"success": True, "data": None, "error": None}


async def _get_user_project(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
    *,
    require_admin: bool = False,
) -> Project:
    """Fetch a project ensuring the user is a member (and optionally an admin)."""
    result = await db.execute(
        select(Project, ProjectMember.role)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(Project.id == project_id, ProjectMember.user_id == user_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    project, member_role = row.tuple()

    if require_admin and member_role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return project
