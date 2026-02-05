"""
Semantic Chunking Service for FinRAG.

Implements intelligent document chunking that:
- Preserves tables as complete chunks
- Splits narrative text into token-based chunks with overlap
- Maintains section header context
"""

import re
from typing import List, Dict, Any, Optional, Tuple
import logging

from app.models.document import DocumentChunk, ChunkType, ChunkingConfig

logger = logging.getLogger(__name__)


class SemanticChunker:
    """
    Semantic document chunker for financial documents.
    
    Handles the intelligent splitting of documents into chunks
    suitable for embedding and retrieval.
    """
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        """
        Initialize chunker with configuration.
        
        Args:
            config: Chunking configuration, uses defaults if not provided
        """
        self.config = config or ChunkingConfig()
        
        # Approximate tokens per character (for English text)
        # GPT tokenizer averages ~4 chars per token
        self.chars_per_token = 4
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in text.
        
        Uses a simple character-based estimation.
        For more accurate results, use tiktoken.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        if not text:
            return 0
        return len(text) // self.chars_per_token
    
    def chunk_document(
        self,
        document_id: str,
        pages_content: List[Dict[str, Any]],
        tables: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """
        Chunk a document into semantic chunks.
        
        Args:
            document_id: Unique document identifier
            pages_content: List of page content dicts from PDF processor
            tables: List of table dicts from PDF processor
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        chunk_index = 0
        
        # Create a map of tables by page
        tables_by_page = {}
        for table in tables:
            page = table.get("page", 1)
            if page not in tables_by_page:
                tables_by_page[page] = []
            tables_by_page[page].append(table)
        
        # Process each page
        for page_data in pages_content:
            page_num = page_data["page_number"]
            text = page_data["text"]
            headers = page_data.get("headers", [])
            
            # Get tables for this page
            page_tables = tables_by_page.get(page_num, [])
            
            # First, add table chunks for this page
            for table in page_tables:
                table_chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_type=ChunkType.TABLE,
                    content=table["text_representation"],
                    page_number=page_num,
                    chunk_index=chunk_index,
                    table_data={
                        "markdown": table.get("markdown"),
                        "rows": table.get("rows"),
                        "columns": table.get("columns"),
                        "headers": table.get("headers"),
                    },
                    table_index=table.get("table_index"),
                    token_count=self.estimate_tokens(table["text_representation"])
                )
                chunks.append(table_chunk)
                chunk_index += 1
            
            # Then chunk the text content
            if text:
                text_chunks = self._chunk_text(
                    document_id=document_id,
                    text=text,
                    page_number=page_num,
                    headers=headers,
                    start_chunk_index=chunk_index
                )
                chunks.extend(text_chunks)
                chunk_index += len(text_chunks)
        
        return chunks
    
    def _chunk_text(
        self,
        document_id: str,
        text: str,
        page_number: int,
        headers: List[Dict[str, Any]],
        start_chunk_index: int
    ) -> List[DocumentChunk]:
        """
        Chunk text content with overlap and header preservation.
        
        Args:
            document_id: Document identifier
            text: Text to chunk
            page_number: Page number
            headers: List of detected headers
            start_chunk_index: Starting index for chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        
        # Calculate target sizes in characters
        target_chars = self.config.target_chunk_size * self.chars_per_token
        overlap_chars = self.config.chunk_overlap * self.chars_per_token
        min_chars = self.config.min_chunk_size * self.chars_per_token
        
        # Split into paragraphs first
        paragraphs = self._split_into_paragraphs(text)
        
        current_chunk = ""
        current_header = None
        chunk_index = start_chunk_index
        
        # Track header positions
        header_positions = {h["position"]: h["text"] for h in headers}
        char_position = 0
        
        for para in paragraphs:
            # Check if this paragraph is a header
            para_stripped = para.strip()
            if char_position in header_positions:
                current_header = header_positions[char_position]
            elif para_stripped in [h["text"] for h in headers]:
                current_header = para_stripped
            
            # Check if adding this paragraph would exceed target
            if len(current_chunk) + len(para) > target_chars and current_chunk:
                # Create chunk from current content
                chunk = self._create_text_chunk(
                    document_id=document_id,
                    content=current_chunk.strip(),
                    page_number=page_number,
                    chunk_index=chunk_index,
                    section_header=current_header,
                    has_overlap_after=True
                )
                chunks.append(chunk)
                chunk_index += 1
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(
                    current_chunk, 
                    overlap_chars
                )
                current_chunk = overlap_text + para
            else:
                current_chunk += para
            
            char_position += len(para)
        
        # Don't forget the last chunk
        if current_chunk.strip():
            # Only add if it meets minimum size or it's the only chunk
            if len(current_chunk) >= min_chars or not chunks:
                chunk = self._create_text_chunk(
                    document_id=document_id,
                    content=current_chunk.strip(),
                    page_number=page_number,
                    chunk_index=chunk_index,
                    section_header=current_header,
                    has_overlap_before=len(chunks) > 0
                )
                chunks.append(chunk)
            elif chunks:
                # Append to previous chunk if too small
                last_chunk = chunks[-1]
                last_chunk.content += "\n" + current_chunk.strip()
                last_chunk.token_count = self.estimate_tokens(last_chunk.content)
        
        # Mark overlap flags
        for i, chunk in enumerate(chunks):
            if i > 0:
                chunk.has_overlap_before = True
            if i < len(chunks) - 1:
                chunk.has_overlap_after = True
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs while preserving structure.
        
        Splits on double newlines primarily, with fallback
        to single newlines for structured content.
        """
        # First try double newlines
        paragraphs = re.split(r'\n\s*\n', text)
        
        result = []
        for para in paragraphs:
            if para.strip():
                result.append(para + "\n\n")
        
        return result
    
    def _get_overlap_text(self, text: str, overlap_chars: int) -> str:
        """
        Get the overlap text from the end of current chunk.
        
        Tries to break at sentence boundaries for cleaner overlap.
        """
        if len(text) <= overlap_chars:
            return text
        
        # Get last overlap_chars characters
        overlap = text[-overlap_chars:]
        
        # Try to find a sentence boundary
        sentence_end = overlap.rfind('. ')
        if sentence_end > len(overlap) // 2:
            overlap = overlap[sentence_end + 2:]
        else:
            # Try word boundary
            word_start = overlap.find(' ')
            if word_start > 0:
                overlap = overlap[word_start + 1:]
        
        return overlap
    
    def _create_text_chunk(
        self,
        document_id: str,
        content: str,
        page_number: int,
        chunk_index: int,
        section_header: Optional[str] = None,
        has_overlap_before: bool = False,
        has_overlap_after: bool = False
    ) -> DocumentChunk:
        """Create a text chunk with all metadata."""
        return DocumentChunk(
            document_id=document_id,
            chunk_type=ChunkType.TEXT,
            content=content,
            page_number=page_number,
            chunk_index=chunk_index,
            section_header=section_header,
            token_count=self.estimate_tokens(content),
            has_overlap_before=has_overlap_before,
            has_overlap_after=has_overlap_after
        )
    
    def get_chunking_stats(
        self, 
        chunks: List[DocumentChunk]
    ) -> Dict[str, Any]:
        """
        Get statistics about the chunking results.
        
        Args:
            chunks: List of document chunks
            
        Returns:
            Dictionary with chunking statistics
        """
        text_chunks = [c for c in chunks if c.chunk_type == ChunkType.TEXT]
        table_chunks = [c for c in chunks if c.chunk_type == ChunkType.TABLE]
        
        text_tokens = sum(c.token_count for c in text_chunks)
        table_tokens = sum(c.token_count for c in table_chunks)
        
        return {
            "total_chunks": len(chunks),
            "text_chunks": len(text_chunks),
            "table_chunks": len(table_chunks),
            "total_tokens": text_tokens + table_tokens,
            "avg_chunk_tokens": (text_tokens + table_tokens) // len(chunks) if chunks else 0,
            "text_tokens": text_tokens,
            "table_tokens": table_tokens,
            "pages_covered": len(set(c.page_number for c in chunks))
        }
