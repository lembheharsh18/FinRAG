"""
Embedding Service for FinRAG.

Generates vector embeddings using ChromaDB's built-in embedding function
(onnxruntime-based, much lighter than PyTorch sentence-transformers).
"""

import logging
from typing import List, Optional
from functools import lru_cache

import numpy as np
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    """
    Embedding service using ChromaDB's default embedding function.
    
    Uses all-MiniLM-L6-v2 via onnxruntime (lightweight, no PyTorch needed).
    Compatible with Render free tier (512MB RAM).
    """
    
    _instance: Optional["EmbeddingService"] = None
    _ef: Optional[DefaultEmbeddingFunction] = None
    
    def __new__(cls):
        """Singleton pattern to reuse the loaded model."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the embedding function."""
        if self._ef is None:
            self._load_model()
    
    def _load_model(self) -> None:
        """Load the ChromaDB default embedding function."""
        logger.info("Loading ChromaDB default embedding function (onnxruntime)")
        
        try:
            self._ef = DefaultEmbeddingFunction()
            logger.info("Successfully loaded embedding function")
        except Exception as e:
            logger.error(f"Failed to load embedding function: {e}")
            raise RuntimeError(f"Failed to load embedding function: {e}")
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        # all-MiniLM-L6-v2 produces 384-dimensional embeddings
        return 384
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")
        
        embeddings = self._ef([text])
        return list(embeddings[0]) if isinstance(embeddings[0], np.ndarray) else embeddings[0]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        
        if not valid_texts:
            raise ValueError("No valid texts to embed")
        
        logger.info(f"Generating embeddings for {len(valid_texts)} texts")
        
        embeddings = self._ef(valid_texts)
        
        return [list(emb) if isinstance(emb, np.ndarray) else emb for emb in embeddings]
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        
        Args:
            query: Query text to embed
            
        Returns:
            Query embedding vector
        """
        return self.embed_text(query)


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    """
    Get cached embedding service instance.
    
    Returns:
        EmbeddingService singleton instance
    """
    return EmbeddingService()
