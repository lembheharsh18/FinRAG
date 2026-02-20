"""
Document models and schemas for the FinRAG application.

Defines Pydantic models for document upload responses,
chunks, and metadata.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


class ChunkType(str, Enum):
    """Type of content chunk."""
    TEXT = "text"
    TABLE = "table"
    HEADER = "header"


class DocumentMetadata(BaseModel):
    """Metadata for an uploaded document."""
    filename: str
    file_size_bytes: int
    page_count: int
    upload_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content_type: str = "application/pdf"
    
    # Processing metadata
    total_chunks: int = 0
    text_chunks: int = 0
    table_chunks: int = 0
    processing_time_seconds: float = 0.0


class DocumentChunk(BaseModel):
    """A single chunk of document content."""
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    chunk_type: ChunkType
    content: str
    
    # Position information
    page_number: int
    chunk_index: int
    
    # For text chunks
    section_header: Optional[str] = None
    token_count: int = 0
    
    # For table chunks
    table_data: Optional[Dict[str, Any]] = None
    table_index: Optional[int] = None
    
    # Overlap tracking
    has_overlap_before: bool = False
    has_overlap_after: bool = False


class DocumentUploadResponse(BaseModel):
    """Response model for successful document upload."""
    document_id: str
    message: str = "Document uploaded and processed successfully"
    metadata: DocumentMetadata
    chunks_preview: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Preview of first few chunks"
    )


class DocumentProcessingError(BaseModel):
    """Error response for document processing failures."""
    error: str
    error_code: str
    details: Optional[Dict[str, Any]] = None


class ChunkingConfig(BaseModel):
    """Configuration for document chunking."""
    target_chunk_size: int = 1024  # tokens (optimised for dense 10-K data)
    chunk_overlap: int = 128  # tokens
    preserve_tables: bool = True
    preserve_headers: bool = True
    min_chunk_size: int = 50  # tokens
