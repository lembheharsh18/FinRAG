"""
PDF Processing Service for FinRAG.

Handles PDF text extraction using pdfplumber and
table extraction using Camelot.
"""

import os
import time
import tempfile
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import logging

import pdfplumber
import camelot
import pandas as pd

from app.models.document import ChunkType

logger = logging.getLogger(__name__)


class PDFProcessingError(Exception):
    """Custom exception for PDF processing errors."""
    def __init__(self, message: str, error_code: str = "PDF_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


# Module-level Ghostscript availability cache
_ghostscript_available: Optional[bool] = None


class PDFProcessor:
    """
    Processes PDF documents to extract text and tables.
    
    Uses pdfplumber for text extraction and Camelot for
    table extraction with support for both lattice and stream modes.
    """
    
    def __init__(self):
        self.supported_extensions = ['.pdf']
    
    def validate_pdf(self, file_path: str) -> bool:
        """
        Validate that the file is a valid PDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            True if valid PDF, raises exception otherwise
        """
        if not os.path.exists(file_path):
            raise PDFProcessingError(
                f"File not found: {file_path}",
                "FILE_NOT_FOUND"
            )
        
        # Check file extension
        ext = Path(file_path).suffix.lower()
        if ext not in self.supported_extensions:
            raise PDFProcessingError(
                f"Unsupported file type: {ext}. Only PDF files are allowed.",
                "INVALID_FILE_TYPE"
            )
        
        # Try to open as PDF to validate
        try:
            with pdfplumber.open(file_path) as pdf:
                if len(pdf.pages) == 0:
                    raise PDFProcessingError(
                        "PDF file has no pages",
                        "EMPTY_PDF"
                    )
        except Exception as e:
            if isinstance(e, PDFProcessingError):
                raise
            raise PDFProcessingError(
                f"Invalid or corrupted PDF file: {str(e)}",
                "INVALID_PDF"
            )
        
        return True
    
    def get_page_count(self, file_path: str) -> int:
        """Get the number of pages in the PDF."""
        with pdfplumber.open(file_path) as pdf:
            return len(pdf.pages)
    
    def extract_text(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from PDF using pdfplumber.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of dicts with page number and extracted text
        """
        pages_content = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    
                    # Extract section headers (lines that look like headers)
                    headers = self._extract_headers(text)
                    
                    pages_content.append({
                        "page_number": page_num,
                        "text": text,
                        "headers": headers,
                        "char_count": len(text),
                        "word_count": len(text.split()) if text else 0
                    })
                    
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise PDFProcessingError(
                f"Failed to extract text: {str(e)}",
                "TEXT_EXTRACTION_ERROR"
            )
        
        return pages_content
    
    def _extract_headers(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract potential section headers from text.
        
        Identifies headers based on common patterns:
        - All caps lines
        - Lines ending with numbers (e.g., "Section 1")
        - Short lines followed by longer content
        """
        headers = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Check for header patterns
            is_header = False
            
            # All caps (with possible numbers)
            if line.isupper() and len(line) > 3 and len(line) < 100:
                is_header = True
            
            # Common financial report headers
            header_keywords = [
                "SUMMARY", "OVERVIEW", "FINANCIAL", "STATEMENT",
                "BALANCE SHEET", "INCOME", "CASH FLOW", "NOTES",
                "MANAGEMENT", "DISCUSSION", "ANALYSIS", "RISK",
                "EXECUTIVE", "QUARTERLY", "ANNUAL", "REPORT"
            ]
            if any(keyword in line.upper() for keyword in header_keywords):
                if len(line) < 150:  # Headers are typically short
                    is_header = True
            
            if is_header:
                headers.append({
                    "text": line,
                    "line_index": i,
                    "position": text.find(line)
                })
        
        return headers
    
    def extract_tables(
        self, 
        file_path: str,
        pages: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        Extract tables from PDF using Camelot.
        
        Tries lattice mode first (for bordered tables),
        then falls back to stream mode (for borderless tables).
        
        Note: Requires Ghostscript to be installed. If not available,
        table extraction will be skipped gracefully.
        
        Args:
            file_path: Path to the PDF file
            pages: Page specification (e.g., "1,2,3" or "all")
            
        Returns:
            List of extracted tables with metadata
        """
        tables = []
        
        # Check if Ghostscript is available (required for Camelot)
        # Use module-level cache to avoid repeated subprocess calls
        global _ghostscript_available
        if _ghostscript_available is False:
            return tables
        
        if _ghostscript_available is None:
            try:
                import subprocess
                gs_found = False
                for gs_cmd in ['gswin64c', 'gswin32c', 'gs']:
                    try:
                        subprocess.run([gs_cmd, '--version'], 
                                       capture_output=True, timeout=5)
                        gs_found = True
                        break
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        continue
                
                _ghostscript_available = gs_found
                if not gs_found:
                    logger.warning(
                        "Ghostscript not found in PATH. Table extraction will be skipped. "
                        "Install Ghostscript and add it to PATH for table extraction support."
                    )
                    return tables
            except Exception as e:
                _ghostscript_available = False
                logger.warning(f"Could not check for Ghostscript: {e}. Skipping table extraction.")
                return tables
        
        # Try lattice mode first (works best for bordered tables)
        try:
            lattice_tables = camelot.read_pdf(
                file_path,
                pages=pages,
                flavor='lattice',
                suppress_stdout=True
            )
            
            for i, table in enumerate(lattice_tables):
                if table.df is not None and not table.df.empty:
                    # Filter bad tables based on Camelot's parsing report
                    report = table.parsing_report
                    if report.get("accuracy", 100) < 80:
                        continue
                    if report.get("whitespace", 0) > 65:
                        continue
                    if len(table.df.columns) <= 1 or len(table.df) <= 1:
                        continue
                        
                    tables.append(self._process_table(
                        table, i, "lattice"
                    ))
                    
        except Exception as e:
            logger.warning(f"Lattice mode failed: {e}")
        
        # Try stream mode for borderless or semi-bordered tables
        try:
            stream_tables = camelot.read_pdf(
                file_path,
                pages=pages,
                flavor='stream',
                suppress_stdout=True
            )
            
            for i, table in enumerate(stream_tables):
                if table.df is not None and not table.df.empty:
                    # Stricter filtering for stream mode to avoid text blocks
                    report = table.parsing_report
                    if report.get("accuracy", 100) < 85:
                        continue
                    if report.get("whitespace", 0) > 65:
                        continue
                    if len(table.df.columns) <= 1 or len(table.df) <= 1:
                        continue
                        
                    # Check for duplicates (same content from lattice)
                    table_dict = self._process_table(
                        table, len(tables) + i, "stream"
                    )
                    if not self._is_duplicate_table(table_dict, tables):
                        tables.append(table_dict)
                        
        except Exception as e:
            logger.warning(f"Stream mode failed: {e}")
        
        return tables
    
    def _process_table(
        self, 
        table, 
        index: int, 
        extraction_method: str
    ) -> Dict[str, Any]:
        """
        Process a Camelot table into a structured format.
        
        Args:
            table: Camelot Table object
            index: Table index
            extraction_method: "lattice" or "stream"
            
        Returns:
            Dictionary with table data and metadata
        """
        df = table.df
        
        # Clean up the dataframe
        df = df.replace(r'\n', ' ', regex=True)
        df = df.replace(r'\s+', ' ', regex=True)
        
        # Convert to various formats
        table_dict = {
            "table_index": index,
            "page": table.page,
            "extraction_method": extraction_method,
            "accuracy": table.accuracy if hasattr(table, 'accuracy') else None,
            "rows": len(df),
            "columns": len(df.columns),
            "data": df.to_dict('records'),
            "markdown": df.to_markdown(index=False),
            "csv": df.to_csv(index=False),
            "headers": list(df.iloc[0]) if len(df) > 0 else [],
        }
        
        # Create a text representation for embedding
        table_dict["text_representation"] = self._table_to_text(df)
        
        return table_dict
    
    def _table_to_text(self, df: pd.DataFrame) -> str:
        """
        Convert a DataFrame to a text representation suitable for embedding.
        
        Creates a natural language description of the table content.
        """
        lines = ["[TABLE START]"]
        
        # Add headers
        if len(df) > 0:
            headers = list(df.iloc[0])
            # Only label as headers if the combined length is reasonable
            # (prevents labeling long text paragraphs as table headers)
            total_len = sum(len(str(h)) for h in headers)
            if total_len < 150:
                lines.append(f"Headers: {', '.join(str(h) for h in headers)}")
            else:
                lines.append(" | ".join(str(h) for h in headers))
        
        # Add row data
        for idx, row in df.iterrows():
            row_text = " | ".join(str(val) for val in row.values)
            lines.append(row_text)
        
        lines.append("[TABLE END]")
        return "\n".join(lines)
    
    def _is_duplicate_table(
        self, 
        new_table: Dict[str, Any], 
        existing_tables: List[Dict[str, Any]]
    ) -> bool:
        """Check if a table is a duplicate of an existing one."""
        new_text = new_table.get("text_representation", "")
        
        for existing in existing_tables:
            existing_text = existing.get("text_representation", "")
            # Simple similarity check
            if new_text == existing_text:
                return True
            # Check if on same page with similar size
            if (existing.get("page") == new_table.get("page") and
                existing.get("rows") == new_table.get("rows") and
                existing.get("columns") == new_table.get("columns")):
                return True
        
        return False
    
    def process_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Complete PDF processing: validate, extract text and tables.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with all extracted content
        """
        # Validate first
        self.validate_pdf(file_path)
        
        # Get basic info
        page_count = self.get_page_count(file_path)
        
        # Extract content
        t0 = time.time()
        pages_content = self.extract_text(file_path)
        logger.info(f"Text extraction: {time.time()-t0:.1f}s ({page_count} pages)")
        
        t1 = time.time()
        tables = self.extract_tables(file_path)
        logger.info(f"Table extraction: {time.time()-t1:.1f}s ({len(tables)} tables)")
        
        return {
            "page_count": page_count,
            "pages": pages_content,
            "tables": tables,
            "total_text_length": sum(p["char_count"] for p in pages_content),
            "total_tables": len(tables)
        }
