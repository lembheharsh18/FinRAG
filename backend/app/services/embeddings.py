"""
Embedding Service for FinRAG.

Uses Google Gemini gemini-embedding-001 for production embeddings.
Falls back to ChromaDB's built-in ONNX embeddings for local development
when GOOGLE_API_KEY is not configured.
"""

import logging
from typing import List, Optional
from functools import lru_cache

import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Embedding dimension constants ────────────────────────────────
GEMINI_EMBEDDING_DIM = 3072
CHROMADB_EMBEDDING_DIM = 384


class EmbeddingService:
    """
    Embedding service with Gemini (production) and ChromaDB ONNX (dev) backends.

    Singleton pattern — reuse a single model instance across the application.
    """

    _instance: Optional["EmbeddingService"] = None
    _backend: Optional[str] = None

    def __new__(cls) -> "EmbeddingService":
        """Singleton pattern to reuse the loaded model."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the embedding backend."""
        if self._backend is None:
            self._load_backend()

    # ── Private ──────────────────────────────────────────────────

    def _load_backend(self) -> None:
        """Load the appropriate embedding backend."""
        # Prefer Google Gemini embeddings
        if settings.google_api_key:
            try:
                from google import genai
                from google.genai import types

                self._client = genai.Client(api_key=settings.google_api_key)
                self._types = types
                # New SDK uses bare model name (no 'models/' prefix)
                raw_name = settings.gemini_embedding_model
                self._model_name = (
                    raw_name.replace("models/", "")
                    if raw_name.startswith("models/")
                    else raw_name
                )
                self._backend = "gemini"
                logger.info(
                    f"Embedding backend: Google Gemini ({self._model_name})"
                )
                return
            except ImportError:
                logger.warning(
                    "google-genai not installed — "
                    "pip install google-genai"
                )
            except Exception as e:
                logger.error(f"Failed to configure Gemini: {e}")

        # Fallback: ChromaDB default ONNX embeddings
        try:
            from chromadb.utils.embedding_functions import (
                DefaultEmbeddingFunction,
            )

            self._ef = DefaultEmbeddingFunction()
            self._backend = "chromadb"
            logger.info(
                "Embedding backend: ChromaDB ONNX (all-MiniLM-L6-v2)"
            )
        except Exception as e:
            logger.error(f"Failed to load any embedding backend: {e}")
            raise RuntimeError(f"No embedding backend available: {e}")

    # ── Public API ───────────────────────────────────────────────

    def get_embedding_dimension(self) -> int:
        """Return the dimensionality of the active embedding model."""
        if self._backend == "gemini":
            return GEMINI_EMBEDDING_DIM
        return CHROMADB_EMBEDDING_DIM

    def embed_text(self, text: str) -> List[float]:
        """
        Generate an embedding for a single text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector as a list of floats.
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        if self._backend == "gemini":
            return self._gemini_embed([text])[0]

        embeddings = self._ef([text])
        return (
            list(embeddings[0])
            if isinstance(embeddings[0], np.ndarray)
            else embeddings[0]
        )

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []

        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("No valid texts to embed")

        logger.info(f"Generating embeddings for {len(valid_texts)} texts")

        if self._backend == "gemini":
            return self._gemini_embed(valid_texts)

        embeddings = self._ef(valid_texts)
        return [
            list(emb) if isinstance(emb, np.ndarray) else emb
            for emb in embeddings
        ]

    def embed_query(self, query: str) -> List[float]:
        """
        Generate an embedding for a search query.

        Uses task_type="RETRIEVAL_QUERY" for Gemini to optimise
        for retrieval use-cases.

        Args:
            query: Query text.

        Returns:
            Query embedding vector.
        """
        if not query or not query.strip():
            raise ValueError("Cannot embed empty query")

        if self._backend == "gemini":
            try:
                result = self._client.models.embed_content(
                    model=self._model_name,
                    contents=query,
                    config=self._types.EmbedContentConfig(
                        task_type="RETRIEVAL_QUERY",
                    ),
                )
                return list(result.embeddings[0].values)
            except Exception as e:
                logger.error(f"Gemini query embedding failed: {e}")
                raise RuntimeError(f"Embedding query failed: {e}")

        return self.embed_text(query)

    # ── Gemini helpers ───────────────────────────────────────────

    def _gemini_embed(self, texts: List[str]) -> List[List[float]]:
        """Batch-embed using Google Gemini with RETRIEVAL_DOCUMENT task type."""
        try:
            # Gemini supports batching via list of content
            BATCH_SIZE = 100  # Gemini limit
            all_embeddings: List[List[float]] = []

            for i in range(0, len(texts), BATCH_SIZE):
                batch = texts[i : i + BATCH_SIZE]
                result = self._client.models.embed_content(
                    model=self._model_name,
                    contents=batch,
                    config=self._types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                    ),
                )
                all_embeddings.extend(
                    [list(e.values) for e in result.embeddings]
                )

            return all_embeddings
        except Exception as e:
            logger.error(f"Gemini batch embedding failed: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}")


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """Get cached embedding service singleton."""
    return EmbeddingService()
