"""
Indexing API endpoints for FinRAG.

Handles document indexing into the vector store
after PDF processing.
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, status, Depends

from app.services.vector_store import VectorStore, VectorStoreError, get_vector_store
from app.services.pdf_processor import PDFProcessor, PDFProcessingError
from app.services.chunking import SemanticChunker
from app.models.document import ChunkingConfig
from app.middleware.auth import get_current_user, get_user_id, AuthenticatedUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Indexing"])


class IndexRequest(BaseModel):
    """Request model for document indexing."""
    document_id: str = Field(..., description="ID of the document to index")
    # user_id is now extracted from auth token


class IndexResponse(BaseModel):
    """Response model for indexing operations."""
    status: str
    message: str
    document_id: str
    user_id: str
    chunks_indexed: int
    collection_total: int


class CollectionStatsResponse(BaseModel):
    """Response model for collection statistics."""
    collection_name: str
    total_chunks: int
    documents: list


# In-memory storage for processed documents (temporary until full DB integration)
# In production, this would be stored in a database
processed_documents: dict = {}


def store_processed_document(document_id: str, data: dict) -> None:
    """Store processed document data temporarily."""
    processed_documents[document_id] = data


def get_processed_document(document_id: str) -> Optional[dict]:
    """Retrieve processed document data."""
    return processed_documents.get(document_id)


@router.post(
    "/index",
    response_model=IndexResponse,
    status_code=status.HTTP_200_OK,
    summary="Index Document",
    description="""
    Index a processed document into the vector store.
    
    This endpoint takes chunks from a previously uploaded document
    and stores them in ChromaDB with embeddings for semantic search.
    
    Each user has their own collection to keep documents separate.
    """,
    responses={
        200: {"description": "Document indexed successfully"},
        404: {"description": "Document not found"},
        422: {"description": "Indexing failed"},
    }
)
async def index_document(
    request: IndexRequest,
    user_id: str = Depends(get_user_id),
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    Index a document's chunks into the vector store.
    
    Args:
        request: Index request with document_id
        user_id: User ID from auth token
        vector_store: Vector store service
        
    Returns:
        IndexResponse with indexing status
    """
    document_id = request.document_id
    
    # Check if document has been processed
    doc_data = get_processed_document(document_id)
    
    if not doc_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": f"Document {document_id} not found. Please upload the document first.",
                "error_code": "DOCUMENT_NOT_FOUND"
            }
        )
    
    chunks = doc_data.get("chunks", [])
    
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Document has no chunks to index",
                "error_code": "NO_CHUNKS"
            }
        )
    
    try:
        result = vector_store.index_chunks(
            user_id=user_id,
            document_id=document_id,
            chunks=chunks
        )
        
        return IndexResponse(
            status=result["status"],
            message=result["message"],
            document_id=document_id,
            user_id=user_id,
            chunks_indexed=result["chunks_indexed"],
            collection_total=result["collection_total"]
        )
        
    except VectorStoreError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": e.message,
                "error_code": e.error_code
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error during indexing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "An unexpected error occurred during indexing",
                "error_code": "INDEXING_ERROR"
            }
        )


@router.get(
    "/collections/stats",
    response_model=CollectionStatsResponse,
    summary="Get Collection Stats",
    description="Get statistics for the authenticated user's document collection."
)
async def get_collection_stats(
    user_id: str = Depends(get_user_id),
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    Get statistics for a user's collection.
    
    Args:
        user_id: User identifier
        vector_store: Vector store service
        
    Returns:
        Collection statistics
    """
    try:
        stats = vector_store.get_collection_stats(user_id)
        documents = vector_store.list_documents(user_id)
        
        return CollectionStatsResponse(
            collection_name=stats["collection_name"],
            total_chunks=stats["total_chunks"],
            documents=documents
        )
    except VectorStoreError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": e.message,
                "error_code": e.error_code
            }
        )


@router.delete(
    "/documents/{document_id}",
    summary="Delete Document from Index",
    description="Remove a document and all its chunks from the vector store."
)
async def delete_document_from_index(
    document_id: str,
    user_id: str = Depends(get_user_id),
    vector_store: VectorStore = Depends(get_vector_store)
):
    """
    Delete a document from the vector store.
    
    Args:
        user_id: User identifier
        document_id: Document to delete
        vector_store: Vector store service
        
    Returns:
        Deletion status
    """
    try:
        result = vector_store.delete_document(user_id, document_id)
        
        # Also remove from processed documents cache
        if document_id in processed_documents:
            del processed_documents[document_id]
        
        return result
    except VectorStoreError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": e.message,
                "error_code": e.error_code
            }
        )
