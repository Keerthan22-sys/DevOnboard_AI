from __future__ import annotations

from app.models.base import Base  # noqa: F401

# Import all models so Base.metadata is fully populated for Alembic
from app.models.user import User  # noqa: F401
from app.models.project import Project, ProjectMember  # noqa: F401
from app.models.document import Document, DocumentChunk  # noqa: F401
from app.models.chat import ChatSession, ChatMessage, AuditLog  # noqa: F401
from app.models.credential import IntegrationCredential  # noqa: F401
