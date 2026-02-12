"""
Vector Store Service for FinRAG.

Handles ChromaDB operations including collection management,
document indexing, and similarity search.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings
from app.models.document import DocumentChunk, ChunkType
from app.services.embeddings import get_embedding_service, EmbeddingService

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStoreError(Exception):
    """Custom exception for vector store errors."""
    def __init__(self, message: str, error_code: str = "VECTOR_STORE_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class VectorStore:
    """
    Vector store service using ChromaDB.
    
    Manages document embeddings with support for:
    - User-specific collections
    - Metadata filtering
    - Similarity search
    """
    
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        """
        Initialize the vector store.
        
        Args:
            embedding_service: Optional embedding service instance
        """
        self.embedding_service = embedding_service or get_embedding_service()
        self._client: Optional[chromadb.ClientAPI] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the ChromaDB client with persistence."""
        persist_dir = Path(settings.chroma_persist_directory)
        persist_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initializing ChromaDB at: {persist_dir}")
        
        try:
            self._client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info("ChromaDB client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise VectorStoreError(
                f"Failed to initialize vector store: {e}",
                "INITIALIZATION_ERROR"
            )
    
    def _get_collection_name(self, user_id: str) -> str:
        """
        Get the collection name for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Sanitized collection name
        """
        # Sanitize user_id for use as collection name
        # ChromaDB collection names must be 3-63 chars, alphanumeric with underscores
        sanitized = "".join(c if c.isalnum() else "_" for c in user_id)
        collection_name = f"user_{sanitized}"
        
        # Ensure valid length
        if len(collection_name) < 3:
            collection_name = f"user_{collection_name}_collection"
        elif len(collection_name) > 63:
            collection_name = collection_name[:63]
        
        return collection_name
    
    def get_or_create_collection(self, user_id: str) -> chromadb.Collection:
        """
        Get or create a collection for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            ChromaDB collection for the user
        """
        collection_name = self._get_collection_name(user_id)
        
        try:
            collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={
                    "user_id": user_id,
                    "description": f"Financial documents for user {user_id}"
                }
            )
            logger.info(f"Using collection: {collection_name}")
            return collection
        except Exception as e:
            logger.error(f"Failed to get/create collection: {e}")
            raise VectorStoreError(
                f"Failed to access collection: {e}",
                "COLLECTION_ERROR"
            )
    
    def index_chunks(
        self,
        user_id: str,
        document_id: str,
        chunks: List[DocumentChunk],
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Index document chunks into the vector store.
        
        Args:
            user_id: User identifier for collection selection
            document_id: Document identifier
            chunks: List of document chunks to index
            
        Returns:
            Dictionary with indexing results
        """
        if not chunks:
            return {
                "status": "skipped",
                "message": "No chunks to index",
                "chunks_indexed": 0
            }
        
        collection = self.get_or_create_collection(user_id)
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            ids.append(chunk.chunk_id)
            documents.append(chunk.content)
            
            metadata = {
                "document_id": document_id,
                "chunk_type": chunk.chunk_type.value,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "has_overlap_before": chunk.has_overlap_before,
                "has_overlap_after": chunk.has_overlap_after,
            }
            
            # Add optional metadata
            if chunk.section_header:
                metadata["section_header"] = chunk.section_header
            if chunk.table_index is not None:
                metadata["table_index"] = chunk.table_index
            if filename:
                metadata["filename"] = filename
            if i == 0:
                import datetime
                metadata["uploaded_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            
            metadatas.append(metadata)
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(documents)} chunks")
        try:
            embeddings = self.embedding_service.embed_texts(documents)
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise VectorStoreError(
                f"Failed to generate embeddings: {e}",
                "EMBEDDING_ERROR"
            )
        
        # Add to ChromaDB
        logger.info(f"Adding {len(chunks)} chunks to collection")
        try:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
        except Exception as e:
            logger.error(f"Failed to add chunks to ChromaDB: {e}")
            raise VectorStoreError(
                f"Failed to index chunks: {e}",
                "INDEXING_ERROR"
            )
        
        # Get collection stats
        collection_count = collection.count()
        
        return {
            "status": "success",
            "message": f"Successfully indexed {len(chunks)} chunks",
            "chunks_indexed": len(chunks),
            "document_id": document_id,
            "collection_total": collection_count
        }
    
    def search(
        self,
        user_id: str,
        query: str,
        n_results: int = 5,
        document_id: Optional[str] = None,
        chunk_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks in the vector store.
        
        Args:
            user_id: User identifier
            query: Search query
            n_results: Number of results to return
            document_id: Optional filter by document
            chunk_type: Optional filter by chunk type ("text" or "table")
            
        Returns:
            List of matching chunks with scores
        """
        collection = self.get_or_create_collection(user_id)
        
        # Generate query embedding
        query_embedding = self.embedding_service.embed_query(query)
        
        # Build where clause for filtering
        where = {}
        if document_id:
            where["document_id"] = document_id
        if chunk_type:
            where["chunk_type"] = chunk_type
        
        # Perform search
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where if where else None,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise VectorStoreError(
                f"Search failed: {e}",
                "SEARCH_ERROR"
            )
        
        # Format results
        formatted_results = []
        if results and results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                formatted_results.append({
                    "chunk_id": chunk_id,
                    "content": results["documents"][0][i] if results["documents"] else None,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                    "similarity_score": 1 - results["distances"][0][i] if results["distances"] else None
                })
        
        return formatted_results
    
    def delete_document(self, user_id: str, document_id: str) -> Dict[str, Any]:
        """
        Delete all chunks for a document.
        
        Args:
            user_id: User identifier
            document_id: Document to delete
            
        Returns:
            Deletion result
        """
        collection = self.get_or_create_collection(user_id)
        
        try:
            # Get chunks for this document
            results = collection.get(
                where={"document_id": document_id},
                include=[]
            )
            
            if results and results["ids"]:
                collection.delete(ids=results["ids"])
                return {
                    "status": "success",
                    "message": f"Deleted {len(results['ids'])} chunks",
                    "chunks_deleted": len(results["ids"]),
                    "document_id": document_id
                }
            else:
                return {
                    "status": "not_found",
                    "message": "Document not found in index",
                    "chunks_deleted": 0,
                    "document_id": document_id
                }
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise VectorStoreError(
                f"Failed to delete document: {e}",
                "DELETION_ERROR"
            )
    
    def get_collection_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics for a user's collection.
        
        Args:
            user_id: User identifier
            
        Returns:
            Collection statistics
        """
        collection = self.get_or_create_collection(user_id)
        
        return {
            "collection_name": collection.name,
            "total_chunks": collection.count(),
            "metadata": collection.metadata
        }
    
    def list_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all documents in a user's collection with rich metadata.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of document info dicts with filename, page_count, chunk_count, etc.
        """
        collection = self.get_or_create_collection(user_id)
        
        try:
            results = collection.get(include=["metadatas"])
            
            if results and results["metadatas"]:
                # Group chunks by document_id and extract metadata
                doc_map: Dict[str, Dict[str, Any]] = {}
                for metadata in results["metadatas"]:
                    if not metadata or "document_id" not in metadata:
                        continue
                    doc_id = metadata["document_id"]
                    if doc_id not in doc_map:
                        doc_map[doc_id] = {
                            "document_id": doc_id,
                            "filename": metadata.get("filename", doc_id),
                            "page_count": 0,
                            "chunk_count": 0,
                            "uploaded_at": metadata.get("uploaded_at"),
                        }
                    doc_map[doc_id]["chunk_count"] += 1
                    page = metadata.get("page_number", 0)
                    if page and page > doc_map[doc_id]["page_count"]:
                        doc_map[doc_id]["page_count"] = page
                
                return list(doc_map.values())
            return []
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []


def get_vector_store() -> VectorStore:
    """
    Get vector store instance.
    
    Returns:
        VectorStore instance
    """
    return VectorStore()
