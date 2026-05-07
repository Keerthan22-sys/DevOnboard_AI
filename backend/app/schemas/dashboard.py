from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProjectStats(BaseModel):
    document_count: int
    chunk_count: int
    query_count: int
    member_count: int
    source_types: dict[str, int]


class ProjectStatsResponse(BaseModel):
    success: bool = True
    data: ProjectStats
    error: str | None = None


class RecentQuery(BaseModel):
    id: UUID
    question: str
    created_at: datetime
    user_name: str


class RecentQueriesResponse(BaseModel):
    success: bool = True
    data: list[RecentQuery]
    error: str | None = None
