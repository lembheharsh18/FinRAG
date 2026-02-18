"""
Retrieval Service for FinRAG.

Handles semantic search, cross-encoder reranking,
and context formatting for the RAG pipeline.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False

from app.services.vector_store import VectorStore, get_vector_store
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class RetrievedChunk:
    """A retrieved chunk with relevance scores."""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    rerank_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "metadata": self.metadata,
            "similarity_score": round(self.similarity_score, 4) if self.similarity_score else None,
            "rerank_score": round(self.rerank_score, 4) if self.rerank_score else None
        }


class RetrievalService:
    """
    Retrieval service for semantic search and reranking.
    
    Combines vector similarity search with optional cross-encoder reranking.
    Reranking is disabled by default to save memory on free-tier hosting.
    """
    
    # Cross-encoder model for reranking
    _cross_encoder = None
    _cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        use_reranking: bool = False  # Disabled by default to save memory
    ):
        """
        Initialize retrieval service.
        
        Args:
            vector_store: Vector store instance
            use_reranking: Whether to use cross-encoder reranking (requires PyTorch)
        """
        self.vector_store = vector_store or get_vector_store()
        self.use_reranking = use_reranking and CROSS_ENCODER_AVAILABLE
        
        if self.use_reranking:
            self._load_cross_encoder()
    
    def _load_cross_encoder(self) -> None:
        """Load cross-encoder model for reranking."""
        if self._cross_encoder is None and CROSS_ENCODER_AVAILABLE:
            logger.info(f"Loading cross-encoder: {self._cross_encoder_model}")
            try:
                self._cross_encoder = CrossEncoder(
                    self._cross_encoder_model,
                    max_length=512
                )
                logger.info("Cross-encoder loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load cross-encoder: {e}. Reranking disabled.")
                self.use_reranking = False
    
    def retrieve(
        self,
        user_id: str,
        query: str,
        n_results: int = 5,
        document_id: Optional[str] = None,
        chunk_type: Optional[str] = None,
        rerank: Optional[bool] = None
    ) -> List[RetrievedChunk]:
        """
        Retrieve relevant chunks for a query.
        
        Args:
            user_id: User identifier
            query: Search query
            n_results: Number of results to return
            document_id: Optional filter by document
            chunk_type: Optional filter by chunk type
            rerank: Override reranking setting
            
        Returns:
            List of retrieved chunks with scores
        """
        # Determine if we should rerank
        should_rerank = rerank if rerank is not None else self.use_reranking
        
        # Get more results if reranking (we'll filter down after)
        fetch_count = n_results * 3 if should_rerank else n_results
        
        # Perform vector search
        logger.info(f"Searching for: '{query[:50]}...' (fetching {fetch_count} candidates)")
        
        search_results = self.vector_store.search(
            user_id=user_id,
            query=query,
            n_results=fetch_count,
            document_id=document_id,
            chunk_type=chunk_type
        )
        
        if not search_results:
            logger.info("No results found")
            return []
        
        # Convert to RetrievedChunk objects
        chunks = [
            RetrievedChunk(
                chunk_id=result["chunk_id"],
                content=result["content"],
                metadata=result["metadata"],
                similarity_score=result["similarity_score"] or 0.0
            )
            for result in search_results
        ]
        
        # Apply cross-encoder reranking
        if should_rerank and self._cross_encoder and len(chunks) > 1:
            chunks = self._rerank_chunks(query, chunks)
        
        # Return top n_results
        return chunks[:n_results]
    
    def _rerank_chunks(
        self,
        query: str,
        chunks: List[RetrievedChunk]
    ) -> List[RetrievedChunk]:
        """
        Rerank chunks using cross-encoder.
        
        Args:
            query: Original query
            chunks: Chunks to rerank
            
        Returns:
            Reranked chunks sorted by relevance
        """
        logger.info(f"Reranking {len(chunks)} chunks with cross-encoder")
        
        # Prepare query-document pairs
        pairs = [(query, chunk.content) for chunk in chunks]
        
        # Get cross-encoder scores
        try:
            scores = self._cross_encoder.predict(pairs)
            
            # Assign rerank scores
            for chunk, score in zip(chunks, scores):
                chunk.rerank_score = float(score)
            
            # Sort by rerank score (higher is better)
            chunks.sort(key=lambda x: x.rerank_score or 0, reverse=True)
            
            logger.info(f"Reranking complete. Top score: {chunks[0].rerank_score:.4f}")
            
        except Exception as e:
            logger.warning(f"Reranking failed: {e}. Using similarity scores.")
        
        return chunks
    
    def format_context(
        self,
        chunks: List[RetrievedChunk],
        max_tokens: int = 3000,
        include_metadata: bool = True
    ) -> str:
        """
        Format retrieved chunks into a context string for the LLM.
        
        Args:
            chunks: Retrieved chunks
            max_tokens: Maximum approximate tokens for context
            include_metadata: Whether to include chunk metadata
            
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant information found in the documents."
        
        context_parts = []
        estimated_tokens = 0
        chars_per_token = 4  # Approximate
        
        for i, chunk in enumerate(chunks, 1):
            # Build chunk context
            chunk_text = ""
            
            if include_metadata:
                metadata = chunk.metadata
                page = metadata.get("page_number", "?")
                chunk_type = metadata.get("chunk_type", "text")
                section = metadata.get("section_header", "")
                
                header = f"[Source {i}: Page {page}"
                if chunk_type == "table":
                    header += ", Table"
                if section:
                    header += f", Section: {section}"
                header += "]"
                
                chunk_text = f"{header}\n{chunk.content}\n"
            else:
                chunk_text = f"[Source {i}]\n{chunk.content}\n"
            
            # Check token limit
            chunk_tokens = len(chunk_text) // chars_per_token
            if estimated_tokens + chunk_tokens > max_tokens:
                # Truncate this chunk if needed
                remaining_chars = (max_tokens - estimated_tokens) * chars_per_token
                if remaining_chars > 200:  # Only add if meaningful
                    chunk_text = chunk_text[:remaining_chars] + "...\n"
                    context_parts.append(chunk_text)
                break
            
            context_parts.append(chunk_text)
            estimated_tokens += chunk_tokens
        
        context = "\n".join(context_parts)
        
        logger.info(f"Formatted context with {len(context_parts)} chunks (~{estimated_tokens} tokens)")
        
        return context
    
    def retrieve_and_format(
        self,
        user_id: str,
        query: str,
        n_results: int = 5,
        document_id: Optional[str] = None,
        max_context_tokens: int = 3000
    ) -> Dict[str, Any]:
        """
        Retrieve chunks and format them for LLM consumption.
        
        Args:
            user_id: User identifier
            query: Search query
            n_results: Number of results
            document_id: Optional document filter
            max_context_tokens: Max tokens for context
            
        Returns:
            Dictionary with chunks and formatted context
        """
        # Retrieve relevant chunks
        chunks = self.retrieve(
            user_id=user_id,
            query=query,
            n_results=n_results,
            document_id=document_id
        )
        
        # Format context
        context = self.format_context(
            chunks=chunks,
            max_tokens=max_context_tokens
        )
        
        return {
            "chunks": [chunk.to_dict() for chunk in chunks],
            "context": context,
            "num_chunks": len(chunks)
        }


def get_retrieval_service() -> RetrievalService:
    """Get retrieval service instance."""
    return RetrievalService()
