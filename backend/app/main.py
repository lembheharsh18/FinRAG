"""
FinRAG - Financial Document QA System

Main FastAPI application entry point with CORS middleware,
rate limiting, structured logging, and API router configuration.
"""

import logging
import logging.config
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import get_settings
from app.api import health
from app.api import documents
from app.api import indexing
from app.api import query
from app.api import answer
from app.api import chat_history
from app.api import evaluation
from app.api import smart_features
from app.api import glossary
from app.api import stocks
from app.api import alerts
from app.api import export_tags

from app.middleware.rate_limiter import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

settings = get_settings()

# ── Structured Logging Configuration ─────────────────────────────
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "format": '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG" if settings.debug else "INFO",
            "formatter": "json" if not settings.debug else "standard",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG" if settings.debug else "INFO",
    },
    "loggers": {
        "uvicorn": {"level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"level": "INFO"},
        "app": {"level": "DEBUG" if settings.debug else "INFO"},
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events for startup and shutdown."""
    logger.info(
        f"Starting {settings.app_name} v{settings.app_version} "
        f"(debug={settings.debug})"
    )

    # Log CORS configuration
    logger.info(f"CORS origins: {settings.cors_origins}")

    # Log active backends
    if settings.pinecone_api_key:
        logger.info("Vector store: Pinecone")
    else:
        logger.info("Vector store: ChromaDB (local)")

    if settings.google_api_key:
        logger.info("Embeddings: Google Gemini")
    else:
        logger.info("Embeddings: ChromaDB ONNX (local)")

    if settings.groq_api_key:
        logger.info(f"LLM: Groq ({settings.groq_model})")
    elif settings.openai_api_key:
        logger.info(f"LLM: OpenAI ({settings.openai_model})")
    else:
        logger.warning("No LLM API key configured")

    yield  # Application runs here
    logger.info("Shutting down FinRAG")


app = FastAPI(
    title=settings.app_name,
    description=(
        "Financial Document QA System — upload, index, and query "
        "financial documents using a RAG pipeline."
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate Limiting ────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "Retry-After"],
)

# ── Global Error Handler ─────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions."""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
        },
    )


# ── Routers ──────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(indexing.router)
app.include_router(query.router)
app.include_router(answer.router)
app.include_router(chat_history.router)
app.include_router(evaluation.router)
app.include_router(smart_features.router)
app.include_router(glossary.router)
app.include_router(stocks.router)
app.include_router(alerts.router)
app.include_router(export_tags.router)


# ── Root endpoint ────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }
