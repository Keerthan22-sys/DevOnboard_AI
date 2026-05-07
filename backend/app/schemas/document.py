from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    source_type: str
    status: str
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    source_type: str
    source_url: str | None
    file_path: str | None
    status: str
    chunk_count: int
    metadata: dict = Field(default_factory=dict, alias="metadata_")
    uploaded_by: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class DocumentListResponse(BaseModel):
    id: UUID
    title: str
    source_type: str
    status: str
    chunk_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ConfluenceIngestRequest(BaseModel):
    url: str
    title: str | None = None


class GithubIngestRequest(BaseModel):
    repo_url: str
    title: str | None = None
    platform: str = "github"  # github or gitlab
