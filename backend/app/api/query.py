"""
Query API endpoints for FinRAG.

Handles document querying and retrieval for the RAG system.
"""

import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, status, Depends

from app.services.retrieval import RetrievalService, get_retrieval_service, RetrievedChunk
from app.middleware.auth import get_current_user, get_user_id, AuthenticatedUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Query"])


class QueryRequest(BaseModel):
    """Request model for document querying."""
    question: str = Field(..., description="The question to ask", min_length=1, max_length=1000)
    document_id: Optional[str] = Field(None, description="Optional: Filter to specific document")
    # user_id is extracted from auth token
    n_results: int = Field(5, description="Number of chunks to retrieve", ge=1, le=20)
    use_reranking: bool = Field(True, description="Whether to use cross-encoder reranking")


class ChunkResult(BaseModel):
    """A single chunk result."""
    chunk_id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: Optional[float]
    rerank_score: Optional[float]


class QueryResponse(BaseModel):
    """Response model for query results."""
    question: str
    chunks: List[ChunkResult]
    context: str
    num_chunks: int
    document_id: Optional[str]


class SearchRequest(BaseModel):
    """Simple search request without full RAG context."""
    query: str = Field(..., description="Search query", min_length=1)
    # user_id is extracted from auth token
    document_id: Optional[str] = Field(None, description="Optional document filter")
    chunk_type: Optional[str] = Field(None, description="Filter by chunk type: 'text' or 'table'")
    n_results: int = Field(5, ge=1, le=50)


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Query Documents",
    description="""
    Query your indexed documents with a natural language question.
    
    This endpoint:
    1. Converts your question into an embedding
    2. Searches ChromaDB for the most relevant chunks
    3. Optionally reranks results using a cross-encoder
    4. Formats the chunks into a context string for the LLM
    
    The returned context can be used directly with GPT-4 for answering.
    """,
    responses={
        200: {"description": "Query successful"},
        400: {"description": "Invalid request"},
        404: {"description": "No documents found"},
    }
)
async def query_documents(
    request: QueryRequest,
    user_id: str = Depends(get_user_id),
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    """
    Query indexed documents to find relevant chunks.
    
    Args:
        request: Query request with question and filters
        retrieval_service: Retrieval service instance
        
    Returns:
        QueryResponse with matching chunks and formatted context
    """
    try:
        # Override reranking setting if specified
        if not request.use_reranking:
            retrieval_service.use_reranking = False
        
        # Retrieve and format
        result = retrieval_service.retrieve_and_format(
            user_id=user_id,
            query=request.question,
            n_results=request.n_results,
            document_id=request.document_id
        )
        
        if result["num_chunks"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "No relevant chunks found. Make sure documents are indexed.",
                    "error_code": "NO_RESULTS"
                }
            )
        
        # Convert chunk dicts to ChunkResult models
        chunk_results = [
            ChunkResult(
                chunk_id=c["chunk_id"],
                content=c["content"],
                metadata=c["metadata"],
                similarity_score=c["similarity_score"],
                rerank_score=c["rerank_score"]
            )
            for c in result["chunks"]
        ]
        
        logger.info(
            f"Query '{request.question[:50]}...' returned {result['num_chunks']} chunks"
        )
        
        return QueryResponse(
            question=request.question,
            chunks=chunk_results,
            context=result["context"],
            num_chunks=result["num_chunks"],
            document_id=request.document_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "An error occurred while processing your query",
                "error_code": "QUERY_ERROR",
                "details": str(e)
            }
        )


@router.post(
    "/search",
    summary="Search Documents",
    description="""
    Simple semantic search across indexed documents.
    
    Returns raw search results without context formatting.
    Useful for exploring document content or debugging.
    """
)
async def search_documents(
    request: SearchRequest,
    user_id: str = Depends(get_user_id),
    retrieval_service: RetrievalService = Depends(get_retrieval_service)
):
    """
    Perform semantic search on indexed documents.
    
    Args:
        request: Search request
        retrieval_service: Retrieval service
        
    Returns:
        List of matching chunks with scores
    """
    try:
        chunks = retrieval_service.retrieve(
            user_id=user_id,
            query=request.query,
            n_results=request.n_results,
            document_id=request.document_id,
            chunk_type=request.chunk_type,
            rerank=False  # Simple search without reranking
        )
        
        return {
            "query": request.query,
            "results": [chunk.to_dict() for chunk in chunks],
            "count": len(chunks)
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Search failed",
                "error_code": "SEARCH_ERROR"
            }
        )


@router.get(
    "/query/test",
    summary="Test Query Endpoint",
    description="Simple test to verify the query endpoint is working."
)
async def test_query():
    """Test endpoint to verify query service is available."""
    return {
        "status": "ok",
        "message": "Query endpoint is ready",
        "endpoints": {
            "POST /api/query": "Full RAG query with context formatting",
            "POST /api/search": "Simple semantic search"
        }
    }
