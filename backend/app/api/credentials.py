from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.credential import IntegrationCredential
from app.models.project import Project
from app.models.user import User
from app.schemas.credential import CredentialCreate, CredentialResponse, CredentialUpdate
from app.utils.encryption import encrypt_value

router = APIRouter(
    prefix="/api/projects/{project_id}/credentials",
    tags=["credentials"],
)

VALID_TYPES = {"github", "gitlab", "confluence"}


async def _get_project_or_404(project_id: UUID, db: AsyncSession) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/", response_model=CredentialResponse, status_code=201)
async def create_credential(
    project_id: UUID,
    data: CredentialCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IntegrationCredential:
    await _get_project_or_404(project_id, db)

    if data.integration_type not in VALID_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"integration_type must be one of: {', '.join(sorted(VALID_TYPES))}",
        )

    if data.integration_type == "confluence" and not data.email:
        raise HTTPException(
            status_code=400,
            detail="email is required for Confluence credentials",
        )

    credential = IntegrationCredential(
        project_id=project_id,
        integration_type=data.integration_type,
        label=data.label,
        encrypted_token=encrypt_value(data.token),
        email=data.email,
        base_url=data.base_url,
        created_by=user.id,
    )
    db.add(credential)
    await db.flush()
    return credential


@router.get("/", response_model=list[CredentialResponse])
async def list_credentials(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[IntegrationCredential]:
    await _get_project_or_404(project_id, db)

    result = await db.execute(
        select(IntegrationCredential)
        .where(IntegrationCredential.project_id == project_id)
        .order_by(IntegrationCredential.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    project_id: UUID,
    credential_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IntegrationCredential:
    await _get_project_or_404(project_id, db)

    result = await db.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.id == credential_id,
            IntegrationCredential.project_id == project_id,
        )
    )
    credential = result.scalar_one_or_none()
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    return credential


@router.put("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    project_id: UUID,
    credential_id: UUID,
    data: CredentialUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IntegrationCredential:
    await _get_project_or_404(project_id, db)

    result = await db.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.id == credential_id,
            IntegrationCredential.project_id == project_id,
        )
    )
    credential = result.scalar_one_or_none()
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    if data.label is not None:
        credential.label = data.label
    if data.token is not None:
        credential.encrypted_token = encrypt_value(data.token)
    if data.email is not None:
        credential.email = data.email
    if data.base_url is not None:
        credential.base_url = data.base_url

    await db.flush()
    return credential


@router.delete("/{credential_id}", status_code=204, response_model=None)
async def delete_credential(
    project_id: UUID,
    credential_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    await _get_project_or_404(project_id, db)

    result = await db.execute(
        select(IntegrationCredential).where(
            IntegrationCredential.id == credential_id,
            IntegrationCredential.project_id == project_id,
        )
    )
    credential = result.scalar_one_or_none()
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")

    await db.delete(credential)
