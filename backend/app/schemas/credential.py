from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CredentialCreate(BaseModel):
    integration_type: str  # github, gitlab, confluence
    label: str
    token: str
    email: str | None = None
    base_url: str | None = None


class CredentialUpdate(BaseModel):
    label: str | None = None
    token: str | None = None
    email: str | None = None
    base_url: str | None = None


class CredentialResponse(BaseModel):
    id: UUID
    project_id: UUID
    integration_type: str
    label: str
    email: str | None
    base_url: str | None
    has_token: bool = True
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
