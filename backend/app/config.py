from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://devonboard:devonboard_secret@localhost:5432/devonboard"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    UPLOAD_DIR: str = "/app/uploads"
    REPO_DIR: str = "/app/repos"
    MAX_FILE_SIZE_MB: int = 50
    EMBEDDING_MODEL: str = "all-mpnet-base-v2"
    RERANK_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    OLLAMA_TIMEOUT: int = 300
    HYDE_ENABLED: bool = False
    CREDENTIAL_ENCRYPTION_KEY: str = ""

    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: str = ""
    CACHE_TTL_LLM: int = 3600  # 1 hour for LLM responses
    CACHE_TTL_RETRIEVAL: int = 1800  # 30 min for retrieval results
    CACHE_TTL_HEALTH: int = 60  # 1 min for health checks
    CACHE_MAX_MEMORY: str = "256mb"
    CACHE_KEY_PREFIX: str = "devonboard"
    CACHE_ENABLED: bool = True

    model_config = {"env_file": ["../.env", ".env"], "extra": "ignore"}


settings = Settings()
