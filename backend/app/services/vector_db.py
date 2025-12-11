"""Vector database service with support for multiple backends."""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import structlog
# import chromadb  # Disabled for Python 3.14 compatibility
# from chromadb.config import Settings
import uuid

from app.core.config import settings
from app.services.faiss_db import FAISSVectorDB

logger = structlog.get_logger(__name__)


class VectorDBInterface(ABC):
    """Abstract interface for vector database operations."""

    @abstractmethod
    async def initialize(self):
        """Initialize the vector database connection."""
        pass

    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents with embeddings to the database."""
        pass

    @abstractmethod
    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        pass

    @abstractmethod
    async def delete_documents(self, document_ids: List[str]):
        """Delete documents by ID."""
        pass

    @abstractmethod
    async def update_document(self, document_id: str, document: Dict[str, Any]):
        """Update a document."""
        pass

    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        pass

    @abstractmethod
    async def count_documents(self) -> int:
        """Get total number of documents."""
        pass

    @abstractmethod
    async def close(self):
        """Close database connection."""
        pass


# ChromaVectorDB disabled for Python 3.14 compatibility
# Use FAISSVectorDB instead


class VectorDBService:
    """
    Main vector database service that handles different backends.
    """

    def __init__(self):
        """Initialize vector database service."""
        self.db: Optional[VectorDBInterface] = None

    async def initialize(self):
        """Initialize the configured vector database backend."""
        db_type = settings.vector_db_type.lower()

        if db_type == "chroma":
            # Use FAISS as ChromaDB replacement for Python 3.14 compatibility
            self.db = FAISSVectorDB()
        # Add more database backends here as needed
        # elif db_type == "qdrant":
        #     self.db = QdrantVectorDB()
        # elif db_type == "pinecone":
        #     self.db = PineconeVectorDB()
        else:
            raise ValueError(f"Unsupported vector database type: {db_type}")

        await self.db.initialize()
        logger.info("Vector database initialized", type="faiss (chroma replacement)")

    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the vector database."""
        if not self.db:
            raise RuntimeError("Vector database not initialized")
        return await self.db.add_documents(documents)

    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        if not self.db:
            raise RuntimeError("Vector database not initialized")
        return await self.db.search(query_embedding, top_k)

    async def delete_documents(self, document_ids: List[str]):
        """Delete documents by ID."""
        if not self.db:
            raise RuntimeError("Vector database not initialized")
        return await self.db.delete_documents(document_ids)

    async def update_document(self, document_id: str, document: Dict[str, Any]):
        """Update a document."""
        if not self.db:
            raise RuntimeError("Vector database not initialized")
        return await self.db.update_document(document_id, document)

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        if not self.db:
            raise RuntimeError("Vector database not initialized")
        return await self.db.get_document(document_id)

    async def count_documents(self) -> int:
        """Get total number of documents."""
        if not self.db:
            raise RuntimeError("Vector database not initialized")
        return await self.db.count_documents()

    async def close(self):
        """Close database connection."""
        if self.db:
            await self.db.close()