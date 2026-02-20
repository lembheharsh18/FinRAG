"""
Vector Store Service for FinRAG.

Uses Pinecone for production vector storage with automatic
fallback to ChromaDB for local development.
"""

import logging
import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

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


# =====================================================================
#  Pinecone Backend
# =====================================================================

class PineconeVectorStore:
    """
    Pinecone-backed vector store.

    Uses Pinecone namespaces for user-level data isolation.
    """

    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedding_service = embedding_service or get_embedding_service()
        self._index = None
        self._initialize()

    def _initialize(self) -> None:
        """Connect to the Pinecone index."""
        try:
            from pinecone import Pinecone

            pc = Pinecone(api_key=settings.pinecone_api_key)

            # Get or create the index
            index_name = settings.pinecone_index_name
            existing = [idx.name for idx in pc.list_indexes()]

            if index_name not in existing:
                from pinecone import ServerlessSpec

                pc.create_index(
                    name=index_name,
                    dimension=self.embedding_service.get_embedding_dimension(),
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud=settings.pinecone_cloud,
                        region=settings.pinecone_region,
                    ),
                )
                logger.info(f"Created Pinecone index: {index_name}")

            self._index = pc.Index(index_name)
            logger.info(f"Connected to Pinecone index: {index_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise VectorStoreError(
                f"Pinecone initialization failed: {e}",
                "INITIALIZATION_ERROR",
            )

    def _namespace(self, user_id: str) -> str:
        """Sanitize user_id into a Pinecone namespace."""
        return "".join(c if c.isalnum() or c == "_" else "_" for c in user_id)

    def index_chunks(
        self,
        user_id: str,
        document_id: str,
        chunks: List[DocumentChunk],
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not chunks:
            return {"status": "skipped", "message": "No chunks to index", "chunks_indexed": 0}

        ns = self._namespace(user_id)
        documents = [c.content for c in chunks]

        logger.info(f"Generating embeddings for {len(documents)} chunks")
        try:
            embeddings = self.embedding_service.embed_texts(documents)
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise VectorStoreError(f"Embedding failed: {e}", "EMBEDDING_ERROR")

        # Build upsert vectors
        vectors = []
        for i, chunk in enumerate(chunks):
            metadata: Dict[str, Any] = {
                "document_id": document_id,
                "chunk_type": chunk.chunk_type.value,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "text": chunk.content[:1000],  # Pinecone metadata text preview
            }
            if chunk.section_header:
                metadata["section_header"] = chunk.section_header
            if chunk.table_index is not None:
                metadata["table_index"] = chunk.table_index
            if filename:
                metadata["filename"] = filename
            if i == 0:
                metadata["uploaded_at"] = datetime.datetime.now(
                    datetime.timezone.utc
                ).isoformat()

            vectors.append({
                "id": chunk.chunk_id,
                "values": embeddings[i],
                "metadata": metadata,
            })

        # Upsert in batches of 100 (Pinecone limits)
        BATCH = 100
        try:
            for start in range(0, len(vectors), BATCH):
                self._index.upsert(
                    vectors=vectors[start : start + BATCH],
                    namespace=ns,
                )
            logger.info(f"Upserted {len(vectors)} vectors to namespace={ns}")
        except Exception as e:
            logger.error(f"Pinecone upsert failed: {e}")
            raise VectorStoreError(f"Upsert failed: {e}", "INDEXING_ERROR")

        stats = self._index.describe_index_stats()
        ns_count = stats.namespaces.get(ns, {})
        total = getattr(ns_count, "vector_count", 0) if ns_count else 0

        return {
            "status": "success",
            "message": f"Indexed {len(vectors)} chunks",
            "chunks_indexed": len(vectors),
            "document_id": document_id,
            "collection_total": total,
        }

    def search(
        self,
        user_id: str,
        query: str,
        n_results: int = 5,
        document_id: Optional[str] = None,
        chunk_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        ns = self._namespace(user_id)
        query_embedding = self.embedding_service.embed_query(query)

        # Build Pinecone filter
        filter_dict: Dict[str, Any] = {}
        if document_id:
            filter_dict["document_id"] = {"$eq": document_id}
        if chunk_type:
            filter_dict["chunk_type"] = {"$eq": chunk_type}

        try:
            results = self._index.query(
                vector=query_embedding,
                top_k=n_results,
                namespace=ns,
                include_metadata=True,
                filter=filter_dict if filter_dict else None,
            )
        except Exception as e:
            logger.error(f"Pinecone query failed: {e}")
            raise VectorStoreError(f"Search failed: {e}", "SEARCH_ERROR")

        formatted = []
        for match in results.get("matches", []):
            meta = match.get("metadata", {})
            formatted.append({
                "chunk_id": match["id"],
                "content": meta.get("text", ""),
                "metadata": {
                    k: v for k, v in meta.items() if k != "text"
                },
                "distance": 1 - match["score"],
                "similarity_score": match["score"],
            })
        return formatted

    def delete_document(self, user_id: str, document_id: str) -> Dict[str, Any]:
        ns = self._namespace(user_id)
        try:
            # Pinecone serverless: delete by metadata filter
            self._index.delete(
                filter={"document_id": {"$eq": document_id}},
                namespace=ns,
            )
            return {
                "status": "success",
                "message": f"Deleted chunks for document {document_id}",
                "document_id": document_id,
            }
        except Exception as e:
            logger.error(f"Pinecone delete failed: {e}")
            raise VectorStoreError(f"Delete failed: {e}", "DELETION_ERROR")

    def get_collection_stats(self, user_id: str) -> Dict[str, Any]:
        ns = self._namespace(user_id)
        try:
            stats = self._index.describe_index_stats()
            ns_stats = stats.namespaces.get(ns, {})
            total = getattr(ns_stats, "vector_count", 0) if ns_stats else 0
            return {
                "collection_name": f"{settings.pinecone_index_name}/{ns}",
                "total_chunks": total,
                "metadata": {"namespace": ns},
            }
        except Exception as e:
            logger.error(f"Stats query failed: {e}")
            return {"collection_name": ns, "total_chunks": 0, "metadata": {}}

    def list_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List documents via a dummy query that returns all vectors.

        Pinecone doesn't support listing metadata natively, so we
        fetch a large top_k with a zero-vector query and group by doc.
        """
        ns = self._namespace(user_id)
        dim = self.embedding_service.get_embedding_dimension()
        try:
            results = self._index.query(
                vector=[0.0] * dim,
                top_k=10000,
                namespace=ns,
                include_metadata=True,
            )
            doc_map: Dict[str, Dict[str, Any]] = {}
            for match in results.get("matches", []):
                meta = match.get("metadata", {})
                doc_id = meta.get("document_id")
                if not doc_id:
                    continue
                if doc_id not in doc_map:
                    doc_map[doc_id] = {
                        "document_id": doc_id,
                        "filename": meta.get("filename", doc_id),
                        "page_count": 0,
                        "chunk_count": 0,
                        "uploaded_at": meta.get("uploaded_at"),
                    }
                doc_map[doc_id]["chunk_count"] += 1
                page = meta.get("page_number", 0)
                if page and page > doc_map[doc_id]["page_count"]:
                    doc_map[doc_id]["page_count"] = page
            return list(doc_map.values())
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            return []


# =====================================================================
#  ChromaDB Backend (local fallback)
# =====================================================================

class ChromaVectorStore:
    """
    ChromaDB-backed vector store — used for local development
    when Pinecone credentials are not set.
    """

    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedding_service = embedding_service or get_embedding_service()
        self._client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        persist_dir = Path(settings.chroma_persist_directory)
        persist_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initializing ChromaDB at: {persist_dir}")
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            self._client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )
            logger.info("ChromaDB client initialized")
        except Exception as e:
            logger.error(f"ChromaDB init failed: {e}")
            raise VectorStoreError(f"ChromaDB init failed: {e}", "INITIALIZATION_ERROR")

    def _collection_name(self, user_id: str) -> str:
        sanitized = "".join(c if c.isalnum() else "_" for c in user_id)
        name = f"user_{sanitized}"
        if len(name) < 3:
            name = f"user_{name}_col"
        return name[:63]

    def get_or_create_collection(self, user_id: str):
        name = self._collection_name(user_id)
        try:
            return self._client.get_or_create_collection(
                name=name,
                metadata={"user_id": user_id},
            )
        except Exception as e:
            raise VectorStoreError(f"Collection error: {e}", "COLLECTION_ERROR")

    def index_chunks(
        self,
        user_id: str,
        document_id: str,
        chunks: List[DocumentChunk],
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not chunks:
            return {"status": "skipped", "message": "No chunks", "chunks_indexed": 0}

        collection = self.get_or_create_collection(user_id)
        ids, documents, metadatas = [], [], []

        for i, chunk in enumerate(chunks):
            ids.append(chunk.chunk_id)
            documents.append(chunk.content)
            meta: Dict[str, Any] = {
                "document_id": document_id,
                "chunk_type": chunk.chunk_type.value,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "has_overlap_before": chunk.has_overlap_before,
                "has_overlap_after": chunk.has_overlap_after,
            }
            if chunk.section_header:
                meta["section_header"] = chunk.section_header
            if chunk.table_index is not None:
                meta["table_index"] = chunk.table_index
            if filename:
                meta["filename"] = filename
            if i == 0:
                meta["uploaded_at"] = datetime.datetime.now(
                    datetime.timezone.utc
                ).isoformat()
            metadatas.append(meta)

        try:
            embeddings = self.embedding_service.embed_texts(documents)
        except Exception as e:
            raise VectorStoreError(f"Embedding failed: {e}", "EMBEDDING_ERROR")

        try:
            collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        except Exception as e:
            raise VectorStoreError(f"Index failed: {e}", "INDEXING_ERROR")

        return {
            "status": "success",
            "message": f"Indexed {len(chunks)} chunks",
            "chunks_indexed": len(chunks),
            "document_id": document_id,
            "collection_total": collection.count(),
        }

    def search(
        self,
        user_id: str,
        query: str,
        n_results: int = 5,
        document_id: Optional[str] = None,
        chunk_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        collection = self.get_or_create_collection(user_id)
        query_embedding = self.embedding_service.embed_query(query)

        where: Dict[str, Any] = {}
        if document_id:
            where["document_id"] = document_id
        if chunk_type:
            where["chunk_type"] = chunk_type

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where if where else None,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            raise VectorStoreError(f"Search failed: {e}", "SEARCH_ERROR")

        formatted = []
        if results and results["ids"] and results["ids"][0]:
            for i, cid in enumerate(results["ids"][0]):
                formatted.append({
                    "chunk_id": cid,
                    "content": results["documents"][0][i] if results["documents"] else None,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None,
                    "similarity_score": 1 - results["distances"][0][i] if results["distances"] else None,
                })
        return formatted

    def delete_document(self, user_id: str, document_id: str) -> Dict[str, Any]:
        collection = self.get_or_create_collection(user_id)
        try:
            results = collection.get(where={"document_id": document_id}, include=[])
            if results and results["ids"]:
                collection.delete(ids=results["ids"])
                return {
                    "status": "success",
                    "message": f"Deleted {len(results['ids'])} chunks",
                    "chunks_deleted": len(results["ids"]),
                    "document_id": document_id,
                }
            return {"status": "not_found", "message": "Document not found", "chunks_deleted": 0, "document_id": document_id}
        except Exception as e:
            raise VectorStoreError(f"Delete failed: {e}", "DELETION_ERROR")

    def get_collection_stats(self, user_id: str) -> Dict[str, Any]:
        collection = self.get_or_create_collection(user_id)
        return {
            "collection_name": collection.name,
            "total_chunks": collection.count(),
            "metadata": collection.metadata,
        }

    def list_documents(self, user_id: str) -> List[Dict[str, Any]]:
        collection = self.get_or_create_collection(user_id)
        try:
            results = collection.get(include=["metadatas"])
            if not results or not results["metadatas"]:
                return []
            doc_map: Dict[str, Dict[str, Any]] = {}
            for meta in results["metadatas"]:
                if not meta or "document_id" not in meta:
                    continue
                did = meta["document_id"]
                if did not in doc_map:
                    doc_map[did] = {
                        "document_id": did,
                        "filename": meta.get("filename", did),
                        "page_count": 0,
                        "chunk_count": 0,
                        "uploaded_at": meta.get("uploaded_at"),
                    }
                doc_map[did]["chunk_count"] += 1
                page = meta.get("page_number", 0)
                if page and page > doc_map[did]["page_count"]:
                    doc_map[did]["page_count"] = page
            return list(doc_map.values())
        except Exception as e:
            logger.error(f"List documents failed: {e}")
            return []


# =====================================================================
#  Unified VectorStore (auto-selects backend)
# =====================================================================

# Type alias for the shared interface
VectorStore = PineconeVectorStore  # default, overridden below

_vector_store_instance: Optional[Any] = None


def get_vector_store():
    """
    Get a vector store instance.

    Automatically selects Pinecone when PINECONE_API_KEY is set,
    otherwise falls back to ChromaDB for local development.
    """
    global _vector_store_instance
    if _vector_store_instance is not None:
        return _vector_store_instance

    if settings.pinecone_api_key:
        logger.info("Using Pinecone vector store")
        _vector_store_instance = PineconeVectorStore()
    else:
        logger.info("Pinecone not configured — using ChromaDB (local)")
        _vector_store_instance = ChromaVectorStore()

    return _vector_store_instance
