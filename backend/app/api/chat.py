from __future__ import annotations

import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.chat import ChatMessage, ChatSession
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.chat import (
    ChatMessageOut,
    ChatRequest,
    ChatResponse,
    ChatResponseData,
    ChatSessionDetailData,
    ChatSessionDetailResponse,
    ChatSessionListResponse,
    ChatSessionOut,
    SourceInfo,
)
from app.services.rag.chain import ask_question

router = APIRouter(prefix="/api/projects", tags=["chat"])


async def _verify_project_access(
    db: AsyncSession,
    project_id: UUID,
    user_id: UUID,
) -> Project:
    """Ensure the user is a member of the project."""
    result = await db.execute(
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(Project.id == project_id, ProjectMember.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ── POST /api/projects/:id/chat ─────────────────────────────────


@router.post("/{project_id}/chat", response_model=ChatResponse)
async def chat(
    project_id: UUID,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatResponse:
    await _verify_project_access(db, project_id, user.id)

    # Resolve or create session
    if body.session_id:
        session = await db.get(ChatSession, body.session_id)
        if not session or session.project_id != project_id or session.user_id != user.id:
            raise HTTPException(status_code=404, detail="Chat session not found")
    else:
        session = ChatSession(
            project_id=project_id,
            user_id=user.id,
            title=body.question[:100],
        )
        db.add(session)
        await db.flush()

    # Save user message
    user_msg = ChatMessage(
        session_id=session.id,
        role="user",
        content=body.question,
        sources=[],
    )
    db.add(user_msg)
    await db.flush()

    # Run RAG pipeline
    start = time.perf_counter()
    rag_result = await ask_question(
        question=body.question,
        project_id=str(project_id),
    )
    latency_ms = int((time.perf_counter() - start) * 1000)

    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=rag_result["answer"],
        sources=rag_result["sources"],
        latency_ms=latency_ms,
    )
    db.add(assistant_msg)
    await db.flush()

    return ChatResponse(
        data=ChatResponseData(
            answer=rag_result["answer"],
            sources=[SourceInfo(**s) for s in rag_result["sources"]],
            session_id=session.id,
            chunks_used=rag_result["chunks_used"],
        ),
    )


# ── GET /api/projects/:id/chat/sessions ─────────────────────────


@router.get("/{project_id}/chat/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatSessionListResponse:
    await _verify_project_access(db, project_id, user.id)

    result = await db.execute(
        select(ChatSession)
        .where(
            ChatSession.project_id == project_id,
            ChatSession.user_id == user.id,
        )
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()

    return ChatSessionListResponse(
        data=[ChatSessionOut.model_validate(s) for s in sessions],
    )


# ── GET /api/projects/:id/chat/sessions/:sid ────────────────────


@router.get(
    "/{project_id}/chat/sessions/{session_id}",
    response_model=ChatSessionDetailResponse,
)
async def get_chat_session(
    project_id: UUID,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatSessionDetailResponse:
    await _verify_project_access(db, project_id, user.id)

    session = await db.get(ChatSession, session_id)
    if not session or session.project_id != project_id or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Chat session not found")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()

    return ChatSessionDetailResponse(
        data=ChatSessionDetailData(
            session=ChatSessionOut.model_validate(session),
            messages=[ChatMessageOut.model_validate(m) for m in messages],
        ),
    )
