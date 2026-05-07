from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.chat import ChatMessage, ChatSession
from app.models.document import Document
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.dashboard import (
    ProjectStats,
    ProjectStatsResponse,
    RecentQueriesResponse,
    RecentQuery,
)

router = APIRouter(prefix="/api/projects", tags=["dashboard"])


async def _verify_project_access(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
) -> Project:
    result = await db.execute(
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(Project.id == project_id, ProjectMember.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ── GET /api/projects/:id/stats ────────────────────────────────


@router.get("/{project_id}/stats", response_model=ProjectStatsResponse)
async def get_project_stats(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProjectStatsResponse:
    await _verify_project_access(db, project_id, user.id)

    # Document count
    doc_count_result = await db.execute(
        select(func.count()).select_from(Document).where(Document.project_id == project_id)
    )
    document_count = doc_count_result.scalar() or 0

    # Chunk count
    chunk_count_result = await db.execute(
        select(func.coalesce(func.sum(Document.chunk_count), 0))
        .where(Document.project_id == project_id)
    )
    chunk_count = chunk_count_result.scalar() or 0

    # Query count (user messages across all sessions in this project)
    query_count_result = await db.execute(
        select(func.count())
        .select_from(ChatMessage)
        .join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .where(
            ChatSession.project_id == project_id,
            ChatMessage.role == "user",
        )
    )
    query_count = query_count_result.scalar() or 0

    # Member count
    member_count_result = await db.execute(
        select(func.count())
        .select_from(ProjectMember)
        .where(ProjectMember.project_id == project_id)
    )
    member_count = member_count_result.scalar() or 0

    # Source types breakdown
    source_type_result = await db.execute(
        select(Document.source_type, func.count())
        .where(Document.project_id == project_id)
        .group_by(Document.source_type)
    )
    source_types = {row[0]: row[1] for row in source_type_result.all()}

    return ProjectStatsResponse(
        data=ProjectStats(
            document_count=document_count,
            chunk_count=int(chunk_count),
            query_count=query_count,
            member_count=member_count,
            source_types=source_types,
        ),
    )


# ── GET /api/projects/:id/recent-queries ───────────────────────


@router.get("/{project_id}/recent-queries", response_model=RecentQueriesResponse)
async def get_recent_queries(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> RecentQueriesResponse:
    await _verify_project_access(db, project_id, user.id)

    result = await db.execute(
        select(ChatMessage.id, ChatMessage.content, ChatMessage.created_at, User.name)
        .join(ChatSession, ChatSession.id == ChatMessage.session_id)
        .join(User, User.id == ChatSession.user_id)
        .where(
            ChatSession.project_id == project_id,
            ChatMessage.role == "user",
        )
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    rows = result.all()

    return RecentQueriesResponse(
        data=[
            RecentQuery(
                id=row.id,
                question=row.content,
                created_at=row.created_at,
                user_name=row.name,
            )
            for row in rows
        ],
    )
