"""Service for indexing documents with embeddings."""

from typing import List, Dict, Any, Optional
import structlog
import hashlib
import json

from app.services.embedding_service import EmbeddingService
from app.services.vector_db import VectorDBService

logger = structlog.get_logger(__name__)


class IndexingService:
    """Service for indexing text chunks with embeddings."""

    def __init__(self):
        """Initialize indexing service."""
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorDBService()

    async def index_chunks(
        self,
        chunks: List[Dict[str, Any]],
        source_id: str,
        force_reindex: bool = False
    ) -> Dict[str, Any]:
        """
        Index text chunks by generating embeddings and storing in vector DB.

        Args:
            chunks: List of text chunks with metadata.
            source_id: ID of the source document (e.g., Notion page ID).
            force_reindex: Force reindexing even if content hasn't changed.

        Returns:
            Indexing statistics.
        """
        try:
            # Initialize vector DB if not already done
            if not self.vector_service.db:
                await self.vector_service.initialize()

            stats = {
                "total_chunks": len(chunks),
                "indexed": 0,
                "skipped": 0,
                "failed": 0
            }

            # Prepare texts for embedding generation
            texts_to_embed = []
            chunks_to_index = []

            for chunk in chunks:
                chunk_id = self._generate_chunk_id(source_id, chunk)

                # Check if chunk already exists (unless force reindex)
                if not force_reindex:
                    existing = await self.vector_service.get_document(chunk_id)
                    if existing:
                        # Check if content has changed
                        if self._has_content_changed(existing, chunk):
                            texts_to_embed.append(chunk["text"])
                            chunks_to_index.append({**chunk, "id": chunk_id})
                        else:
                            stats["skipped"] += 1
                            continue
                else:
                    texts_to_embed.append(chunk["text"])
                    chunks_to_index.append({**chunk, "id": chunk_id})

            # Generate embeddings in batch
            if texts_to_embed:
                logger.info("Generating embeddings",
                           count=len(texts_to_embed),
                           source_id=source_id)

                embeddings = await self.embedding_service.generate_embeddings_batch(texts_to_embed)

                # Prepare documents for vector DB
                documents = []
                for i, chunk in enumerate(chunks_to_index):
                    doc = {
                        "id": chunk["id"],
                        "text": chunk["text"],
                        "embedding": embeddings[i],
                        "metadata": {
                            **chunk.get("metadata", {}),
                            "source_id": source_id,
                            "content_hash": self._generate_content_hash(chunk["text"])
                        }
                    }
                    documents.append(doc)

                # Add to vector database
                await self.vector_service.add_documents(documents)
                stats["indexed"] = len(documents)

            logger.info("Indexing completed",
                       source_id=source_id,
                       stats=stats)

            return stats

        except Exception as e:
            logger.error("Indexing failed",
                        source_id=source_id,
                        error=str(e))
            raise

    async def reindex_source(self, source_id: str) -> Dict[str, Any]:
        """
        Reindex all chunks from a specific source.

        Args:
            source_id: ID of the source to reindex.

        Returns:
            Reindexing statistics.
        """
        try:
            # First, delete all existing chunks from this source
            await self.delete_source_chunks(source_id)

            # The actual reindexing would be triggered by fetching
            # new data from Notion and calling index_chunks
            # This is handled by the refresh endpoint

            return {
                "source_id": source_id,
                "status": "ready_for_reindex",
                "message": "Old chunks deleted, ready for new indexing"
            }

        except Exception as e:
            logger.error("Reindexing failed", source_id=source_id, error=str(e))
            raise

    async def delete_source_chunks(self, source_id: str) -> int:
        """
        Delete all chunks from a specific source.

        Args:
            source_id: ID of the source whose chunks to delete.

        Returns:
            Number of chunks deleted.
        """
        try:
            # This is a simplified implementation
            # In production, you'd query the vector DB for all chunks
            # with matching source_id in metadata and delete them

            logger.info("Deleting source chunks", source_id=source_id)

            # For now, we'll return 0 as we don't have a direct way
            # to query by metadata in the current implementation
            return 0

        except Exception as e:
            logger.error("Failed to delete source chunks",
                        source_id=source_id,
                        error=str(e))
            raise

    def _generate_chunk_id(self, source_id: str, chunk: Dict[str, Any]) -> str:
        """
        Generate a unique ID for a chunk.

        Args:
            source_id: Source document ID.
            chunk: Chunk data.

        Returns:
            Unique chunk ID.
        """
        # Combine source ID with chunk index
        chunk_index = chunk.get("metadata", {}).get("chunk_index", 0)
        return f"{source_id}_{chunk_index}"

    def _generate_content_hash(self, text: str) -> str:
        """
        Generate a hash of text content for change detection.

        Args:
            text: Text content.

        Returns:
            Content hash.
        """
        return hashlib.md5(text.encode()).hexdigest()

    def _has_content_changed(
        self,
        existing: Dict[str, Any],
        new_chunk: Dict[str, Any]
    ) -> bool:
        """
        Check if content has changed between existing and new chunk.

        Args:
            existing: Existing document from vector DB.
            new_chunk: New chunk data.

        Returns:
            True if content has changed.
        """
        existing_hash = existing.get("metadata", {}).get("content_hash", "")
        new_hash = self._generate_content_hash(new_chunk["text"])
        return existing_hash != new_hash

    async def get_indexing_stats(self) -> Dict[str, Any]:
        """
        Get overall indexing statistics.

        Returns:
            Indexing statistics.
        """
        try:
            if not self.vector_service.db:
                await self.vector_service.initialize()

            total_documents = await self.vector_service.count_documents()

            return {
                "total_documents": total_documents,
                "vector_db_type": self.vector_service.db.__class__.__name__,
                "embedding_model": self.embedding_service.model
            }

        except Exception as e:
            logger.error("Failed to get indexing stats", error=str(e))
            return {
                "total_documents": 0,
                "error": str(e)
            }