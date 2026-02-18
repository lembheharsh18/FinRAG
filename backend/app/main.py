"""
FinRAG - Financial Document QA System

Main FastAPI application entry point with CORS middleware,
health check endpoints, and API router configuration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.api import health
from app.api import documents
from app.api import indexing
from app.api import query
from app.api import answer
from app.api import stocks
from app.api import smart_features
from app.api import export_tags
from app.api import alerts
from app.api import chat_history
from app.api import evaluation
from app.api import glossary


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events for the application.
    Use this for initializing database connections, loading models, etc.
    """
    # Startup: Initialize resources
    print(f"[*] Starting {settings.app_name} v{settings.app_version}")
    print(f"[*] Debug mode: {settings.debug}")
    
    # LLM provider diagnostics
    if settings.groq_api_key:
        print(f"[*] LLM Provider: Groq")
        print(f"[*] Groq model: {settings.groq_model}")
        print(f"[*] Groq key: {settings.groq_api_key[:8]}...")
    elif settings.openai_api_key:
        print(f"[*] LLM Provider: OpenAI")
        print(f"[*] OpenAI model: {settings.openai_model}")
    else:
        print("[!] WARNING: No LLM API key configured!")
    
    print(f"[*] Using embedding model: {settings.embedding_model}")
    
    yield
    
    # Shutdown: Clean up resources
    print(f"[*] Shutting down {settings.app_name}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    ## FinRAG - RAG-based Financial Document QA System
    
    A powerful question-answering system designed for retail investors
    to query and understand financial documents using AI.
    
    ### Features:
    - 📄 PDF document upload and processing
    - 🔍 Semantic search across financial documents
    - 💬 Natural language Q&A with GPT-4
    - 📊 Support for tables and financial data extraction
    - 📈 Live stock market dashboard
    
    ### Tech Stack:
    - FastAPI for the backend API
    - ChromaDB for vector storage
    - OpenAI GPT-4 for question answering
    - Sentence Transformers for embeddings
    """,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers
app.include_router(health.router, tags=["Health"])
app.include_router(documents.router)
app.include_router(indexing.router)
app.include_router(query.router)
app.include_router(answer.router)
app.include_router(stocks.router)
app.include_router(smart_features.router)
app.include_router(export_tags.router)
app.include_router(alerts.router)
app.include_router(chat_history.router)
app.include_router(evaluation.router)
app.include_router(glossary.router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint returning application information.
    """
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "description": "RAG-based Financial Document QA System for Retail Investors",
        "docs": "/docs",
        "health": "/health"
    }
