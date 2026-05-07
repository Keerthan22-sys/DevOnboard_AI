from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class IntegrationCredential(Base):
    __tablename__ = "integration_credentials"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    integration_type: Mapped[str] = mapped_column(String(50), nullable=False)  # github, gitlab, confluence
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_token: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), default=None)  # Required for Confluence
    base_url: Mapped[str | None] = mapped_column(String(500), default=None)  # For self-hosted instances
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
