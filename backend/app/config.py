"""
Configuration module for the FinRAG application.

Loads settings from environment variables (and .env file via python-dotenv).
"""

import os
import json
from functools import lru_cache
from typing import Optional
from dotenv import load_dotenv

load_dotenv(encoding="utf-8")


def _env(key: str, default: str = "") -> str:
    """Read an env var (case-insensitive on Windows, exact on Linux)."""
    return os.environ.get(key, os.environ.get(key.upper(), default))


def _env_optional(key: str) -> Optional[str]:
    """Read an optional env var, returning None if unset/empty."""
    val = _env(key, "")
    return val if val else None


def _env_bool(key: str, default: bool = False) -> bool:
    """Read an env var as a boolean."""
    val = _env(key, "").lower()
    if val in ("1", "true", "yes"):
        return True
    if val in ("0", "false", "no"):
        return False
    return default


def _env_int(key: str, default: int = 0) -> int:
    """Read an env var as an integer."""
    val = _env(key, "")
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _parse_cors(raw: str) -> list[str]:
    """Parse a CORS origins string (JSON array, comma-separated, or single URL)."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [s.strip() for s in parsed]
    except (json.JSONDecodeError, TypeError):
        pass
    return [s.strip() for s in raw.split(",") if s.strip()]


class Settings:
    """
    Application settings loaded from environment variables.

    Covers: app metadata, LLM providers, vector DB, embeddings,
    file storage, authentication, security, and rate limiting.
    """

    def __init__(self) -> None:
        # ── Application ──────────────────────────────────────────
        self.app_name: str = _env("APP_NAME", "FinRAG")
        self.app_version: str = _env("APP_VERSION", "2.0.0")
        self.debug: bool = _env_bool("DEBUG", False)

        # ── LLM — Groq (preferred) ──────────────────────────────
        self.groq_api_key: Optional[str] = _env_optional("GROQ_API_KEY")
        self.groq_model: str = _env("GROQ_MODEL", "llama-3.3-70b-versatile")

        # ── LLM — OpenAI (fallback) ─────────────────────────────
        self.openai_api_key: Optional[str] = _env_optional("OPENAI_API_KEY")
        self.openai_model: str = _env("OPENAI_MODEL", "gpt-4")
        self.llm_base_url: Optional[str] = _env_optional("LLM_BASE_URL")

        # ── Google Gemini Embeddings ─────────────────────────────
        self.google_api_key: Optional[str] = _env_optional("GOOGLE_API_KEY")
        self.gemini_embedding_model: str = _env(
            "GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"
        )

        # ── Pinecone Vector Store ────────────────────────────────
        self.pinecone_api_key: Optional[str] = _env_optional("PINECONE_API_KEY")
        self.pinecone_index_name: str = _env("PINECONE_INDEX_NAME", "finrag")
        self.pinecone_cloud: str = _env("PINECONE_CLOUD", "aws")
        self.pinecone_region: str = _env("PINECONE_REGION", "us-east-1")

        # ── ChromaDB (local dev fallback) ────────────────────────
        self.chroma_persist_directory: str = _env("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
        self.chroma_collection_name: str = _env("CHROMA_COLLECTION_NAME", "financial_documents")

        # ── Embedding Model (legacy, used only when Gemini not set)
        self.embedding_model: str = _env("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

        # ── AWS S3 File Storage ──────────────────────────────────
        self.aws_access_key_id: Optional[str] = _env_optional("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key: Optional[str] = _env_optional("AWS_SECRET_ACCESS_KEY")
        self.aws_s3_bucket_name: Optional[str] = _env_optional("AWS_S3_BUCKET_NAME")
        self.aws_region: str = _env("AWS_REGION", "us-east-1")

        # ── CORS ─────────────────────────────────────────────────
        _default_cors = (
            "https://fin-rag-phi.vercel.app,"
            "https://finrag-ss76.onrender.com,"
            "http://localhost:5173,"
            "http://localhost:3000"
        )
        self.cors_origins: list[str] = _parse_cors(_env("CORS_ORIGINS", _default_cors))

        # ── File Upload ──────────────────────────────────────────
        self.max_file_size_mb: int = _env_int("MAX_FILE_SIZE_MB", 50)
        self.allowed_extensions: list[str] = [".pdf"]
        self.upload_directory: str = _env("UPLOAD_DIRECTORY", "./uploads")

        # ── Authentication (Firebase / Supabase) ─────────────────
        self.auth_provider: str = _env("AUTH_PROVIDER", "firebase")
        self.auth_disabled: bool = _env_bool("AUTH_DISABLED", False)

        # Firebase
        self.firebase_project_id: Optional[str] = _env_optional("FIREBASE_PROJECT_ID")
        self.firebase_service_account_path: Optional[str] = _env_optional("FIREBASE_SERVICE_ACCOUNT_PATH")
        self.firebase_service_account_json: Optional[str] = _env_optional("FIREBASE_SERVICE_ACCOUNT_JSON")

        # Supabase (alternative)
        self.supabase_url: Optional[str] = _env_optional("SUPABASE_URL")
        self.supabase_anon_key: Optional[str] = _env_optional("SUPABASE_ANON_KEY")
        self.supabase_service_role_key: Optional[str] = _env_optional("SUPABASE_SERVICE_ROLE_KEY")

        # ── Security ─────────────────────────────────────────────
        self.api_secret_key: Optional[str] = _env_optional("API_SECRET_KEY")

        # ── Rate Limiting ────────────────────────────────────────
        self.rate_limit_default: str = _env("RATE_LIMIT_DEFAULT", "60/minute")
        self.rate_limit_upload: str = _env("RATE_LIMIT_UPLOAD", "10/minute")
        self.rate_limit_answer: str = _env("RATE_LIMIT_ANSWER", "30/minute")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are only loaded once
    and reused throughout the application lifecycle.

    Returns:
        Settings: Application settings instance
    """
    return Settings()
