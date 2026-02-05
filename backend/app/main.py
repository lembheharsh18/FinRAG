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


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events for the application.
    Use this for initializing database connections, loading models, etc.
    """
    # Startup: Initialize resources
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"📊 Debug mode: {settings.debug}")
    print(f"🤖 Using OpenAI model: {settings.openai_model}")
    print(f"🧠 Using embedding model: {settings.embedding_model}")
    
    yield
    
    # Shutdown: Clean up resources
    print(f"👋 Shutting down {settings.app_name}")


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
