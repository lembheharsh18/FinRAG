"""
Document upload and processing API endpoints.

Handles PDF file uploads, validation, processing,
and chunking for the FinRAG system.
"""

import os
import uuid
import time
import shutil
import tempfile
from typing import Optional
from pathlib import Path
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from fastapi.responses import JSONResponse

from app.config import get_settings, Settings
from app.models.document import (
    DocumentUploadResponse,
    DocumentMetadata,
    DocumentProcessingError,
    ChunkingConfig,
)
from app.services.pdf_processor import PDFProcessor, PDFProcessingError
from app.services.chunking import SemanticChunker
from app.api.indexing import store_processed_document
from app.middleware.auth import get_current_user, get_user_id, AuthenticatedUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Documents"])


def get_pdf_processor() -> PDFProcessor:
    """Dependency injection for PDF processor."""
    return PDFProcessor()


def get_chunker() -> SemanticChunker:
    """Dependency injection for semantic chunker."""
    config = ChunkingConfig(
        target_chunk_size=500,
        chunk_overlap=50,
        preserve_tables=True,
        preserve_headers=True
    )
    return SemanticChunker(config)


def validate_file_size(file: UploadFile, settings: Settings) -> None:
    """
    Validate that the uploaded file is within size limits.
    
    Args:
        file: Uploaded file
        settings: Application settings
        
    Raises:
        HTTPException: If file exceeds size limit
    """
    # Get file size by reading content length or seeking
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Seek back to start
    
    max_size_bytes = settings.max_file_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": f"File too large. Maximum size is {settings.max_file_size_mb}MB",
                "error_code": "FILE_TOO_LARGE",
                "details": {
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "max_size_mb": settings.max_file_size_mb
                }
            }
        )


def validate_file_type(file: UploadFile, settings: Settings) -> None:
    """
    Validate that the uploaded file type is allowed.
    
    Args:
        file: Uploaded file
        settings: Application settings
        
    Raises:
        HTTPException: If file type is not allowed
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Filename is required",
                "error_code": "MISSING_FILENAME"
            }
        )
    
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "error": f"File type '{file_ext}' is not supported",
                "error_code": "UNSUPPORTED_FILE_TYPE",
                "details": {
                    "allowed_extensions": settings.allowed_extensions,
                    "provided_extension": file_ext
                }
            }
        )


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF Document",
    description="""
    Upload a PDF document for processing.
    
    The document will be:
    1. Validated for file type and size
    2. Parsed to extract text content
    3. Analyzed for tables using both lattice and stream detection
    4. Split into semantic chunks for retrieval
    
    Returns a document_id that can be used for querying.
    """,
    responses={
        201: {"description": "Document processed successfully"},
        400: {"description": "Invalid request or file"},
        413: {"description": "File too large"},
        415: {"description": "Unsupported file type"},
        422: {"description": "Failed to process PDF"},
    }
)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    user: AuthenticatedUser = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    pdf_processor: PDFProcessor = Depends(get_pdf_processor),
    chunker: SemanticChunker = Depends(get_chunker),
):
    """
    Upload and process a PDF document.
    
    Args:
        file: PDF file to upload
        settings: Application settings
        pdf_processor: PDF processing service
        chunker: Semantic chunking service
        
    Returns:
        DocumentUploadResponse with document_id and metadata
    """
    start_time = time.time()
    
    # Validate file
    validate_file_type(file, settings)
    validate_file_size(file, settings)
    
    # Generate unique document ID
    document_id = str(uuid.uuid4())
    
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.upload_directory)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Save file temporarily for processing
    temp_file_path = None
    try:
        # Create temp file with proper extension
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=".pdf",
            dir=upload_dir
        ) as temp_file:
            temp_file_path = temp_file.name
            
            # Write uploaded content to temp file
            content = await file.read()
            temp_file.write(content)
        
        # Get file size
        file_size = os.path.getsize(temp_file_path)
        
        # Process the PDF
        try:
            pdf_content = pdf_processor.process_pdf(temp_file_path)
        except PDFProcessingError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": e.message,
                    "error_code": e.error_code
                }
            )
        
        # Chunk the document
        chunks = chunker.chunk_document(
            document_id=document_id,
            pages_content=pdf_content["pages"],
            tables=pdf_content["tables"]
        )
        
        # Get chunking statistics
        chunk_stats = chunker.get_chunking_stats(chunks)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create metadata
        metadata = DocumentMetadata(
            filename=file.filename,
            file_size_bytes=file_size,
            page_count=pdf_content["page_count"],
            total_chunks=chunk_stats["total_chunks"],
            text_chunks=chunk_stats["text_chunks"],
            table_chunks=chunk_stats["table_chunks"],
            processing_time_seconds=round(processing_time, 2)
        )
        
        # Create preview of first few chunks
        chunks_preview = [
            {
                "chunk_id": c.chunk_id,
                "type": c.chunk_type.value,
                "page": c.page_number,
                "tokens": c.token_count,
                "preview": c.content[:200] + "..." if len(c.content) > 200 else c.content
            }
            for c in chunks[:5]  # First 5 chunks
        ]
        
        # Store chunks for later indexing (keep for backwards compatibility)
        store_processed_document(document_id, {
            "chunks": chunks,
            "metadata": metadata.model_dump(),
            "filename": file.filename
        })
        
        # Auto-index the document immediately
        # This eliminates the need for a separate /api/index call
        user_id = user.user_id
        try:
            from app.services.vector_store import VectorStore
            vector_store = VectorStore()
            index_result = vector_store.index_chunks(
                user_id=user_id,
                document_id=document_id,
                chunks=chunks
            )
            logger.info(
                f"Auto-indexed document {document_id}: "
                f"{index_result['chunks_indexed']} chunks indexed"
            )
            indexed = True
            chunks_indexed = index_result['chunks_indexed']
        except Exception as index_error:
            logger.warning(f"Auto-indexing failed (will retry via /api/index): {index_error}")
            indexed = False
            chunks_indexed = 0
        
        logger.info(
            f"Processed document {document_id}: "
            f"{metadata.page_count} pages, {metadata.total_chunks} chunks"
        )
        
        response = DocumentUploadResponse(
            document_id=document_id,
            message="Document uploaded and processed successfully" + (" and indexed" if indexed else ""),
            metadata=metadata,
            chunks_preview=chunks_preview
        )
        
        # Add indexing info to response (will be ignored by model but useful)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "An unexpected error occurred while processing the document",
                "error_code": "PROCESSING_ERROR",
                "details": {"message": str(e)}
            }
        )
    finally:
        # Clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file: {e}")


@router.get(
    "/documents/{document_id}",
    summary="Get Document Info",
    description="Retrieve information about a processed document."
)
async def get_document(document_id: str):
    """
    Get information about a processed document.
    
    Note: Full implementation will query ChromaDB for stored document info.
    """
    # TODO: Implement document retrieval from ChromaDB
    return {
        "document_id": document_id,
        "status": "Document storage not yet implemented",
        "message": "This endpoint will return document details once ChromaDB integration is complete"
    }
