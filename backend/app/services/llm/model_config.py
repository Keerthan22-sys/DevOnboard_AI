from __future__ import annotations

from app.config import settings

# Default model configuration for Ollama LLM calls.
MODEL_CONFIG: dict = {
    "model": settings.OLLAMA_MODEL,
    "options": {
        "temperature": 0.1,
        "top_p": 0.9,
        "num_predict": 2048,
    },
}

EMBEDDING_CONFIG: dict = {
    "model_name": settings.EMBEDDING_MODEL,
    "dimension": 384,  # all-MiniLM-L6-v2 output dimension
}
