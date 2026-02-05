"""
Embedding Service for FinRAG.

Generates vector embeddings using sentence-transformers
for semantic search and retrieval.
"""

import logging
from typing import List, Optional
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    """
    Embedding service using sentence-transformers.
    
    Uses the all-MiniLM-L6-v2 model by default for fast,
    high-quality embeddings suitable for semantic search.
    """
    
    _instance: Optional["EmbeddingService"] = None
    _model: Optional[SentenceTransformer] = None
    
    def __new__(cls):
        """Singleton pattern to reuse the loaded model."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the embedding model."""
        if self._model is None:
            self._load_model()
    
    def _load_model(self) -> None:
        """Load the sentence transformer model."""
        model_name = settings.embedding_model
        logger.info(f"Loading embedding model: {model_name}")
        
        try:
            self._model = SentenceTransformer(model_name)
            logger.info(f"Successfully loaded embedding model: {model_name}")
            logger.info(f"Embedding dimension: {self.get_embedding_dimension()}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise RuntimeError(f"Failed to load embedding model: {e}")
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings."""
        return self._model.get_sentence_embedding_dimension()
    
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
        
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
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
        
        embeddings = self._model.encode(
            valid_texts,
            convert_to_numpy=True,
            show_progress_bar=len(valid_texts) > 10
        )
        
        return [emb.tolist() for emb in embeddings]
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        
        Uses the same method as embed_text, but provides
        semantic clarity for query embeddings.
        
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
