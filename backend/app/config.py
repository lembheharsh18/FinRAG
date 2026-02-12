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
    
    Attributes:
        app_name: Name of the application
        debug: Debug mode flag
        openai_api_key: OpenAI API key for GPT-4 access
        chroma_persist_directory: Directory for ChromaDB persistence
        embedding_model: Sentence transformer model for embeddings
        cors_origins: Allowed origins for CORS
    """
    
    # Application Settings
    app_name: str = "FinRAG"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # OpenAI Configuration (legacy, still supported)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    
    # Groq Configuration (preferred - free and fast)
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"
    
    # Generic LLM config (auto-detected from above)
    llm_base_url: Optional[str] = None
    
    # ChromaDB Configuration
    chroma_persist_directory: str = "./chroma_db"
    chroma_collection_name: str = "financial_documents"
    
    # Embedding Model Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # CORS Configuration
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"]
    
    # File Upload Configuration
    max_file_size_mb: int = 50
    allowed_extensions: list[str] = [".pdf"]
    upload_directory: str = "./uploads"
    
    # Authentication (Firebase/Supabase)
    auth_provider: str = "firebase"  # or "supabase"
    auth_disabled: bool = False  # Set to True to disable auth in development
    
    # Firebase Configuration
    firebase_project_id: Optional[str] = None
    firebase_service_account_path: Optional[str] = None  # Path to service account JSON
    firebase_service_account_json: Optional[str] = None  # Service account JSON as string
    
    # Supabase Configuration (alternative to Firebase)
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_role_key: Optional[str] = None
    
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
