"""
Configuration module for the FinRAG application.

This module handles all environment variable loading and configuration
settings using Pydantic's BaseSettings for type validation and
automatic environment variable loading.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Covers: app metadata, LLM providers, vector DB, embeddings,
    file storage, authentication, security, and rate limiting.
    """

    # ── Application ──────────────────────────────────────────────
    app_name: str = "FinRAG"
    app_version: str = "2.0.0"
    debug: bool = False

    # ── LLM — Groq (preferred) ───────────────────────────────────
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"

    # ── LLM — OpenAI (fallback) ──────────────────────────────────
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    llm_base_url: Optional[str] = None

    # ── Google Gemini Embeddings ─────────────────────────────────
    google_api_key: Optional[str] = None
    gemini_embedding_model: str = "models/gemini-embedding-001"

    # ── Pinecone Vector Store ────────────────────────────────────
    pinecone_api_key: Optional[str] = None
    pinecone_index_name: str = "finrag"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"

    # ── ChromaDB (local dev fallback) ────────────────────────────
    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "financial_documents"

    # ── Embedding Model (legacy, used only when Gemini not set) ──
    embedding_model: str = "all-MiniLM-L6-v2"

    # ── AWS S3 File Storage ──────────────────────────────────────
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_s3_bucket_name: Optional[str] = None
    aws_region: str = "us-east-1"

    # ── CORS ─────────────────────────────────────────────────────
    cors_origins: list[str] = [
        '*',
        'localhost:5173',
        'localhost:3000',
        'finrag-phi.vercel.app',
        'finrag-ss76.onrender.com',
    ]

    # ── File Upload ──────────────────────────────────────────────
    max_file_size_mb: int = 50
    allowed_extensions: list[str] = [".pdf"]
    upload_directory: str = "./uploads"

    # ── Authentication (Firebase / Supabase) ─────────────────────
    auth_provider: str = "firebase"
    auth_disabled: bool = False

    # Firebase
    firebase_project_id: Optional[str] = None
    firebase_service_account_path: Optional[str] = None
    firebase_service_account_json: Optional[str] = None

    # Supabase (alternative)
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None

    # ── Security ─────────────────────────────────────────────────
    api_secret_key: Optional[str] = None  # Used for SHA256 webhook verification

    # ── Rate Limiting ────────────────────────────────────────────
    rate_limit_default: str = "60/minute"
    rate_limit_upload: str = "10/minute"
    rate_limit_answer: str = "30/minute"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


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
