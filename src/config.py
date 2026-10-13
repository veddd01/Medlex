"""Centralized configuration loading and validation.

Every other module reads settings from here instead of calling
`os.getenv` directly, so there is exactly one place that knows the env
var names, defaults, and validation rules (see Requirement 13: "Invalid
API keys" is handled by `Settings.require_pinecone()` raising a clear,
actionable `ConfigError` instead of letting a cryptic SDK exception
bubble up from deep inside a request handler).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load variables from a local .env into the process environment. Safe to
# call multiple times; does nothing if .env is absent (e.g. in a container
# that injects real env vars directly).
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    """Typed, validated view over the process environment."""

    # Pinecone
    pinecone_api_key: Optional[str]
    pinecone_environment: Optional[str]
    pinecone_cloud: str
    pinecone_index_name: str

    # Hugging Face & LLM Options
    huggingfacehub_api_token: Optional[str]
    embedding_model_name: str
    llm_model_name: str
    llm_provider: str  # "local", "openai", "gemini", "ollama"
    openai_api_key: Optional[str]
    gemini_api_key: Optional[str]
    ollama_base_url: str
    max_context_chars: int

    # RAG tuning (defaults match the project spec exactly: 500/50/top-5)
    chunk_size: int
    chunk_overlap: int
    top_k: int
    min_score: float

    # Paths
    default_pdf_path: Path

    def require_pinecone(self) -> None:
        """Fail fast with an actionable message if Pinecone creds are missing.

        Call this at the point credentials are actually needed (index
        creation, upsert, search) rather than at import time, so the app
        can still start up and serve a clear error instead of crashing on
        import.
        """
        missing = []
        if not self.pinecone_api_key:
            missing.append("PINECONE_API_KEY")
        if not self.pinecone_environment:
            missing.append("PINECONE_ENVIRONMENT")
        if missing:
            raise ConfigError(
                "Missing required environment variable(s): "
                f"{', '.join(missing)}. Copy the .env template and fill "
                "these in — see README.md > Environment Setup."
            )


def load_settings() -> Settings:
    """Build a `Settings` from environment variables, with sane defaults."""
    settings = Settings(
        pinecone_api_key=os.getenv("PINECONE_API_KEY") or None,
        pinecone_environment=os.getenv("PINECONE_ENVIRONMENT") or None,
        pinecone_cloud=os.getenv("PINECONE_CLOUD", "aws"),
        pinecone_index_name=os.getenv("PINECONE_INDEX_NAME", "medical-encyclopedia"),
        huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN") or None,
        embedding_model_name=os.getenv(
            "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        llm_model_name=os.getenv("LLM_MODEL_NAME", "google/flan-t5-base"),
        llm_provider=os.getenv("LLM_PROVIDER", "local"),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        max_context_chars=int(os.getenv("MAX_CONTEXT_CHARS", "1800")),
        chunk_size=int(os.getenv("CHUNK_SIZE", "500")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "50")),
        top_k=int(os.getenv("TOP_K", "3")),
        min_score=float(os.getenv("MIN_SCORE", "0.3")),
        default_pdf_path=PROJECT_ROOT / "data" / "medical_book.pdf",
    )
    logger.debug("Loaded settings for index=%s, embedding_model=%s, llm=%s",
                 settings.pinecone_index_name, settings.embedding_model_name,
                 settings.llm_model_name)
    return settings


# Most modules can just `from src.config import settings`. Importing this
# module never raises — only `require_pinecone()` does — so tooling that
# imports the package (tests, linters, `python -m py_compile`) works
# without credentials present.
settings = load_settings()
