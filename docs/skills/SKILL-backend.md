---
name: backend-fastapi
description: "Python FastAPI backend development for DevOnboard AI. Use this skill for ALL backend tasks: creating API endpoints, SQLAlchemy models, Pydantic schemas, database operations, auth logic, middleware, and service layer code. Triggers on any mention of backend, API, endpoint, route, model, schema, migration, database, auth, JWT, FastAPI, or Python server code."
---

# Backend FastAPI Development — DevOnboard AI

## Environment

- Python 3.12+, FastAPI 0.104+, SQLAlchemy 2.0 (async), Alembic, Pydantic v2
- PostgreSQL 16 via asyncpg
- Always use `from __future__ import annotations` at top of every file

## Config Pattern

```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://devonboard:password@localhost:5432/devonboard"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    UPLOAD_DIR: str = "/app/uploads"
    REPO_DIR: str = "/app/repos"
    MAX_FILE_SIZE_MB: int = 50
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    model_config = {"env_file": ".env"}

settings = Settings()
```

## Database Session Pattern

```python
# backend/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## SQLAlchemy Model Pattern

Every model must follow this exact pattern. No deviations.

```python
# backend/app/models/user.py
from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="developer")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

## Pydantic Schema Pattern

Use Pydantic v2 syntax. Never use class Config — use model_config dict.

```python
# backend/app/schemas/user.py
from __future__ import annotations
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
```

## API Endpoint Pattern

Every endpoint follows this structure. Consistent response format.

```python
# backend/app/api/auth.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.utils.auth import hash_password, verify_password, create_token
from app.models.user import User
from sqlalchemy import select

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check existing user
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=data.email,
        name=data.name,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    await db.flush()

    token = create_token(user_id=str(user.id))
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )
```

## Dependency Injection — Auth Guard

```python
# backend/app/api/deps.py
from __future__ import annotations
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.utils.auth import verify_token
from app.models.user import User
from sqlalchemy import select

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await db.execute(select(User).where(User.id == payload["user_id"]))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
```

## FastAPI App Setup

```python
# backend/app/main.py
from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, projects, documents, chat, dashboard

app = FastAPI(title="DevOnboard AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(dashboard.router)

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "devonboard-ai"}
```

## Requirements.txt — Exact Versions

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.1
pydantic[email]==2.10.4
pydantic-settings==2.7.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.20
httpx==0.28.1
beautifulsoup4==4.12.3
pdfplumber==0.11.4
chromadb==0.5.23
sentence-transformers==3.3.1
langchain==0.3.14
langchain-community==0.3.14
llama-index==0.12.5
gitpython==3.1.44
structlog==24.4.0
python-dotenv==1.0.1
```

## Error Handling Pattern

```python
from fastapi import HTTPException

# Use specific status codes
raise HTTPException(status_code=400, detail="Invalid input")
raise HTTPException(status_code=401, detail="Not authenticated")
raise HTTPException(status_code=403, detail="Not authorized")
raise HTTPException(status_code=404, detail="Resource not found")
raise HTTPException(status_code=409, detail="Conflict — resource exists")
raise HTTPException(status_code=500, detail="Internal server error")
```

## File Upload Pattern

```python
from fastapi import UploadFile, File
import shutil
from pathlib import Path

@router.post("/api/projects/{project_id}/documents/upload")
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    upload_dir = Path(settings.UPLOAD_DIR) / project_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Then create Document record, trigger ingestion...
```

## Alembic Async Setup

In alembic/env.py, use this pattern for async:

```python
from app.database import engine
from app.models.user import Base  # Import all models here

target_metadata = Base.metadata

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()

def run_migrations_online():
    import asyncio
    asyncio.run(run_async_migrations())
```
