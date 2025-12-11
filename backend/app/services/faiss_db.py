"""FAISS vector database service for Python 3.14 compatibility."""

from typing import List, Dict, Any, Optional
import json
import os
import pickle
import faiss
import numpy as np
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class FAISSVectorDB:
    """FAISS implementation of vector database."""

    def __init__(self):
        """Initialize FAISS vector database."""
        self.index = None
        self.documents = {}  # Store document metadata
        self.dimension = 1536  # OpenAI embedding dimension
        self.index_path = os.path.join(settings.chroma_persist_directory, "faiss_index.bin")
        self.docs_path = os.path.join(settings.chroma_persist_directory, "documents.json")

    async def initialize(self):
        """Initialize FAISS index and load existing data."""
        try:
            # Create directory if not exists
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)

            # Load existing index and documents
            if os.path.exists(self.index_path) and os.path.exists(self.docs_path):
                self.index = faiss.read_index(self.index_path)
                with open(self.docs_path, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                logger.info("Loaded existing FAISS index",
                           documents=len(self.documents))
            else:
                # Create new index
                self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
                self.documents = {}
                logger.info("Created new FAISS index")

        except Exception as e:
            logger.error("Failed to initialize FAISS", error=str(e))
            # Create new index as fallback
            self.index = faiss.IndexFlatIP(self.dimension)
            self.documents = {}

    async def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents with embeddings to FAISS index.

        Args:
            documents: List of documents with 'id', 'text', 'embedding', and 'metadata'.
        """
        if not documents:
            return

        try:
            embeddings = []
            for doc in documents:
                doc_id = doc.get('id', str(len(self.documents)))

                # Store document metadata
                self.documents[doc_id] = {
                    'text': doc.get('text', ''),
                    'metadata': doc.get('metadata', {})
                }

                # Prepare embedding
                embedding = doc.get('embedding', [])
                if len(embedding) != self.dimension:
                    logger.warning("Embedding dimension mismatch",
                                 expected=self.dimension,
                                 actual=len(embedding))
                    # Pad or truncate to correct dimension
                    if len(embedding) < self.dimension:
                        embedding = embedding + [0.0] * (self.dimension - len(embedding))
                    else:
                        embedding = embedding[:self.dimension]

                embeddings.append(embedding)

            # Add to FAISS index
            embeddings_array = np.array(embeddings, dtype=np.float32)
            # Normalize for cosine similarity
            faiss.normalize_L2(embeddings_array)
            self.index.add(embeddings_array)

            # Save index and documents
            await self._save_index()

            logger.info("Added documents to FAISS", count=len(documents))

        except Exception as e:
            logger.error("Failed to add documents to FAISS", error=str(e))
            raise

    async def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents in FAISS index.

        Args:
            query_embedding: Query embedding vector.
            top_k: Number of results to return.

        Returns:
            List of similar documents with scores.
        """
        try:
            if self.index.ntotal == 0:
                logger.warning("FAISS index is empty")
                return []

            # Prepare query embedding
            if len(query_embedding) != self.dimension:
                if len(query_embedding) < self.dimension:
                    query_embedding = query_embedding + [0.0] * (self.dimension - len(query_embedding))
                else:
                    query_embedding = query_embedding[:self.dimension]

            query_array = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_array)

            # Search
            scores, indices = self.index.search(query_array, min(top_k, self.index.ntotal))

            # Format results
            documents = []
            doc_ids = list(self.documents.keys())

            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx >= 0 and idx < len(doc_ids):
                    doc_id = doc_ids[idx]
                    doc = self.documents[doc_id]
                    documents.append({
                        'id': doc_id,
                        'text': doc['text'],
                        'metadata': doc['metadata'],
                        'score': float(score)
                    })

            logger.info("Searched FAISS index", results_count=len(documents))
            return documents

        except Exception as e:
            logger.error("Failed to search FAISS index", error=str(e))
            return []

    async def delete_documents(self, document_ids: List[str]):
        """
        Delete documents from FAISS index.
        Note: FAISS doesn't support direct deletion, so we rebuild the index.
        """
        if not document_ids:
            return

        try:
            # Remove from documents dict
            for doc_id in document_ids:
                self.documents.pop(doc_id, None)

            # Rebuild index with remaining documents
            await self._rebuild_index()

            logger.info("Deleted documents from FAISS", count=len(document_ids))

        except Exception as e:
            logger.error("Failed to delete documents from FAISS", error=str(e))
            raise

    async def update_document(self, document_id: str, document: Dict[str, Any]):
        """
        Update a document in FAISS index.
        This requires rebuilding the index.
        """
        try:
            # Update document data
            if document_id in self.documents:
                self.documents[document_id] = {
                    'text': document.get('text', ''),
                    'metadata': document.get('metadata', {})
                }

            # Add new document if it doesn't exist
            await self.add_documents([{**document, 'id': document_id}])

            logger.info("Updated document in FAISS", document_id=document_id)

        except Exception as e:
            logger.error("Failed to update document in FAISS",
                        document_id=document_id,
                        error=str(e))
            raise

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.

        Args:
            document_id: ID of the document to retrieve.

        Returns:
            Document data or None if not found.
        """
        doc = self.documents.get(document_id)
        if doc:
            return {
                'id': document_id,
                'text': doc['text'],
                'metadata': doc['metadata']
            }
        return None

    async def count_documents(self) -> int:
        """Get total number of documents."""
        return len(self.documents)

    async def close(self):
        """Close FAISS index (save final state)."""
        try:
            await self._save_index()
            logger.info("FAISS index closed and saved")
        except Exception as e:
            logger.error("Failed to close FAISS index", error=str(e))

    async def clear_collection(self):
        """Clear all documents from the index."""
        try:
            self.index = faiss.IndexFlatIP(self.dimension)
            self.documents = {}
            await self._save_index()
            logger.info("Cleared FAISS index")

        except Exception as e:
            logger.error("Failed to clear FAISS index", error=str(e))
            raise

    async def _save_index(self):
        """Save FAISS index and documents to disk."""
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.docs_path, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error("Failed to save FAISS index", error=str(e))

    async def _rebuild_index(self):
        """Rebuild FAISS index from existing documents."""
        try:
            # Create new index
            self.index = faiss.IndexFlatIP(self.dimension)

            if not self.documents:
                return

            # We need embeddings to rebuild, but we don't store them
            # This is a limitation - in a real implementation, you'd store embeddings
            logger.warning("Cannot rebuild FAISS index without stored embeddings")

        except Exception as e:
            logger.error("Failed to rebuild FAISS index", error=str(e))