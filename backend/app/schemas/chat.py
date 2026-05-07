from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── Request schemas ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    session_id: UUID | None = None


# ── Nested response types ───────────────────────────────────────

class SourceInfo(BaseModel):
    document_id: str
    section_title: str
    source_url: str | None = None
    page_number: int | None = None
    relevance_score: float


class ChatMessageOut(BaseModel):
    id: UUID
    role: str
    content: str
    sources: list[SourceInfo] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Top-level response schemas ──────────────────────────────────

class ChatResponse(BaseModel):
    success: bool = True
    data: ChatResponseData
    error: str | None = None


class ChatResponseData(BaseModel):
    answer: str
    sources: list[SourceInfo]
    session_id: UUID
    chunks_used: int


class ChatSessionOut(BaseModel):
    id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionListResponse(BaseModel):
    success: bool = True
    data: list[ChatSessionOut]
    error: str | None = None


class ChatSessionDetailResponse(BaseModel):
    success: bool = True
    data: ChatSessionDetailData
    error: str | None = None


class ChatSessionDetailData(BaseModel):
    session: ChatSessionOut
    messages: list[ChatMessageOut]
