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
import threading
from typing import Optional
from pathlib import Path
import logging

from fastapi import APIRouter, UploadFile, File, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse, FileResponse

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
from app.middleware.rate_limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Documents"])


def get_pdf_processor() -> PDFProcessor:
    """Dependency injection for PDF processor."""
    return PDFProcessor()


def get_chunker() -> SemanticChunker:
    """Dependency injection for semantic chunker."""
    config = ChunkingConfig(
        target_chunk_size=1024,
        chunk_overlap=128,
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
@limiter.limit(get_settings().rate_limit_upload)
async def upload_document(
    request: Request,
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
    
    # Create per-user upload directory
    user_id = user.user_id
    upload_dir = Path(settings.upload_directory) / user_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Persistent file path for this document
    persistent_path = upload_dir / f"{document_id}.pdf"
    
    try:
        # Write uploaded content to persistent file
        content = await file.read()
        with open(persistent_path, "wb") as f:
            f.write(content)
        
        # Get file size
        file_size = os.path.getsize(persistent_path)
        
        # Process the PDF
        try:
            pdf_content = pdf_processor.process_pdf(str(persistent_path))
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
        
        # Auto-index in background thread so upload returns fast
        def _background_index():
            try:
                from app.services.vector_store import VectorStore
                t0 = time.time()
                vector_store = VectorStore()
                index_result = vector_store.index_chunks(
                    user_id=user_id,
                    document_id=document_id,
                    chunks=chunks,
                    filename=file.filename
                )
                logger.info(
                    f"Background-indexed document {document_id}: "
                    f"{index_result['chunks_indexed']} chunks in {time.time()-t0:.1f}s"
                )
            except Exception as index_error:
                logger.warning(f"Background indexing failed (retry via /api/index): {index_error}")

        threading.Thread(target=_background_index, daemon=True).start()
        
        logger.info(
            f"Processed document {document_id}: "
            f"{metadata.page_count} pages, {metadata.total_chunks} chunks "
            f"in {time.time()-start_time:.1f}s (indexing in background)"
        )
        
        response = DocumentUploadResponse(
            document_id=document_id,
            message="Document uploaded and processed successfully. Indexing in background.",
            metadata=metadata,
            chunks_preview=chunks_preview
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing document: {e}")
        # Clean up persistent file on error
        if persistent_path.exists():
            try:
                os.unlink(persistent_path)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "An unexpected error occurred while processing the document",
                "error_code": "PROCESSING_ERROR",
                "details": {"message": str(e)}
            }
        )


@router.get(
    "/documents/{document_id}/file",
    summary="Get Document PDF",
    description="Serve the original PDF file for preview/download."
)
async def get_document_file(
    document_id: str,
    user_id: str = Depends(get_user_id),
    settings: Settings = Depends(get_settings),
):
    """
    Serve the uploaded PDF file.
    
    Args:
        document_id: Document identifier
        user_id: Authenticated user's ID
        settings: App settings
        
    Returns:
        The PDF file content
    """
    upload_dir = Path(settings.upload_directory) / user_id
    file_path = upload_dir / f"{document_id}.pdf"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Document file not found",
                "error_code": "FILE_NOT_FOUND"
            }
        )
    
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"{document_id}.pdf"
    )
