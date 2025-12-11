"""Pinecone vector database service."""

from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import structlog

from app.core.config import settings
from app.services.vector_db import VectorDBInterface

logger = structlog.get_logger(__name__)

try:
    import pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False
    logger.warning("Pinecone not available - install with: pip install pinecone-client")


class PineconeVectorDB(VectorDBInterface):
    """Pinecone-based vector database implementation."""

    def __init__(self):
        """Initialize Pinecone vector database."""
        self.index = None
        self.index_name = settings.pinecone_index_name
        self.dimension = 1536  # OpenAI embedding dimension

    async def initialize(self):
        """Initialize Pinecone connection and index."""
        if not PINECONE_AVAILABLE:
            raise RuntimeError("Pinecone client not available. Install with: pip install pinecone-client")

        if not settings.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")

        try:
            # Initialize Pinecone (v2.2.4 API)
            pinecone.init(
                api_key=settings.pinecone_api_key,
                environment="us-east-1-aws"  # Free tier environment
            )

            # Check if index exists, create if not
            if self.index_name not in pinecone.list_indexes():
                logger.info(f"Creating Pinecone index: {self.index_name}")
                pinecone.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine"
                )

            # Get index reference
            self.index = pinecone.Index(self.index_name)
            logger.info("Pinecone index initialized successfully", index=self.index_name)

        except Exception as e:
            logger.error("Failed to initialize Pinecone", error=str(e))
            raise

    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents with embeddings to Pinecone."""
        if not self.index:
            raise RuntimeError("Pinecone index not initialized")

        try:
            vectors = []
            for doc in documents:
                vector_id = doc.get("id", str(uuid.uuid4()))
                embedding = doc.get("embedding")
                metadata = {
                    "text": doc.get("text", "")[:1000],  # Pinecone metadata limit
                    "page_id": doc.get("page_id", ""),
                    "chunk_index": doc.get("chunk_index", 0),
                    "created_at": datetime.utcnow().isoformat()
                }

                if embedding:
                    vectors.append({
                        "id": vector_id,
                        "values": embedding,
                        "metadata": metadata
                    })

            # Batch upsert to Pinecone
            if vectors:
                batch_size = 100  # Pinecone recommended batch size
                for i in range(0, len(vectors), batch_size):
                    batch = vectors[i:i + batch_size]
                    self.index.upsert(vectors=batch)

                logger.info("Documents added to Pinecone", count=len(vectors))
                return len(vectors)

        except Exception as e:
            logger.error("Failed to add documents to Pinecone", error=str(e))
            raise

    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents in Pinecone."""
        if not self.index:
            raise RuntimeError("Pinecone index not initialized")

        try:
            response = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )

            results = []
            for match in response.matches:
                result = {
                    "id": match.id,
                    "text": match.metadata.get("text", ""),
                    "page_id": match.metadata.get("page_id", ""),
                    "score": float(match.score),
                    "metadata": match.metadata
                }
                results.append(result)

            logger.info("Pinecone search completed", results_count=len(results))
            return results

        except Exception as e:
            logger.error("Failed to search Pinecone", error=str(e))
            raise

    async def delete_documents(self, document_ids: List[str]):
        """Delete documents from Pinecone by ID."""
        if not self.index:
            raise RuntimeError("Pinecone index not initialized")

        try:
            self.index.delete(ids=document_ids)
            logger.info("Documents deleted from Pinecone", count=len(document_ids))
        except Exception as e:
            logger.error("Failed to delete documents from Pinecone", error=str(e))
            raise

    async def update_document(self, document_id: str, document: Dict[str, Any]):
        """Update a document in Pinecone."""
        # Pinecone doesn't have direct update - upsert instead
        await self.add_documents([{**document, "id": document_id}])

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID from Pinecone."""
        if not self.index:
            raise RuntimeError("Pinecone index not initialized")

        try:
            response = self.index.fetch(ids=[document_id])
            if document_id in response.vectors:
                vector = response.vectors[document_id]
                return {
                    "id": document_id,
                    "text": vector.metadata.get("text", ""),
                    "page_id": vector.metadata.get("page_id", ""),
                    "metadata": vector.metadata
                }
            return None
        except Exception as e:
            logger.error("Failed to get document from Pinecone", error=str(e))
            return None

    async def count_documents(self) -> int:
        """Get total number of documents in Pinecone."""
        if not self.index:
            raise RuntimeError("Pinecone index not initialized")

        try:
            stats = self.index.describe_index_stats()
            return stats['total_vector_count']
        except Exception as e:
            logger.error("Failed to count documents in Pinecone", error=str(e))
            return 0

    async def close(self):
        """Close Pinecone connection."""
        # Pinecone client doesn't require explicit closing
        logger.info("Pinecone connection closed")

    async def clear_index(self):
        """Clear all vectors from Pinecone index."""
        if not self.index:
            raise RuntimeError("Pinecone index not initialized")

        try:
            self.index.delete(delete_all=True)
            logger.info("Pinecone index cleared")
        except Exception as e:
            logger.error("Failed to clear Pinecone index", error=str(e))
            raise