"""RAG (Retrieval-Augmented Generation) query service."""

from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
import structlog
from datetime import datetime

from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.vector_db import VectorDBService

logger = structlog.get_logger(__name__)


class RAGService:
    """Service for RAG-based query processing."""

    def __init__(self):
        """Initialize RAG service."""
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorDBService()
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def query(
        self,
        query: str,
        top_k: int = 5,
        temperature: float = 0.7,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """
        Process a query using RAG.

        Args:
            query: Natural language query.
            top_k: Number of relevant documents to retrieve.
            temperature: LLM temperature for response generation.
            max_tokens: Maximum tokens for response.

        Returns:
            Query result with answer and sources.
        """
        try:
            # Initialize services if needed
            if not self.vector_service.db:
                await self.vector_service.initialize()

            # Set default max_tokens if not provided
            if max_tokens is None:
                max_tokens = settings.max_tokens

            # Generate query embedding
            logger.info("Generating query embedding", query=query[:100])
            query_embedding = await self.embedding_service.generate_query_embedding(query)

            # Search for relevant documents
            logger.info("Searching for relevant documents", top_k=top_k)
            relevant_docs = await self.vector_service.search(
                query_embedding,
                top_k=top_k
            )

            if not relevant_docs:
                logger.warning("No relevant documents found", query=query[:100])
                return {
                    "answer": "죄송합니다. 질문과 관련된 정보를 찾을 수 없습니다. Notion 문서를 먼저 인덱싱해 주세요.",
                    "sources": [],
                    "model_used": settings.openai_model_chat,
                    "query": query
                }

            # Prepare context from relevant documents
            context = self._prepare_context(relevant_docs)

            # Generate answer using GPT
            logger.info("Generating answer with GPT", model=settings.openai_model_chat)
            answer = await self._generate_answer(
                query,
                context,
                temperature,
                max_tokens
            )

            # Format sources
            sources = self._format_sources(relevant_docs)

            result = {
                "answer": answer,
                "sources": sources,
                "model_used": settings.openai_model_chat,
                "query": query,
                "timestamp": datetime.utcnow().isoformat()
            }

            logger.info("Query processed successfully",
                       query_length=len(query),
                       answer_length=len(answer),
                       sources_count=len(sources))

            return result

        except Exception as e:
            logger.error("RAG query failed", error=str(e), query=query[:100])
            raise

    def _prepare_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Prepare context from retrieved documents.

        Args:
            documents: List of relevant documents.

        Returns:
            Formatted context string.
        """
        context_parts = []

        for i, doc in enumerate(documents, 1):
            text = doc.get("text", "")
            score = doc.get("score", 0.0)
            metadata = doc.get("metadata", {})

            # Include document metadata in context
            page_title = metadata.get("page_title", "Untitled")

            context_part = f"[문서 {i} - {page_title} (관련도: {score:.2f})]\n{text}"
            context_parts.append(context_part)

        context = "\n\n---\n\n".join(context_parts)
        return context

    async def _generate_answer(
        self,
        query: str,
        context: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        Generate answer using GPT with retrieved context.

        Args:
            query: User query.
            context: Retrieved context.
            temperature: Generation temperature.
            max_tokens: Maximum tokens for response.

        Returns:
            Generated answer.
        """
        try:
            # Prepare messages for GPT
            system_prompt = """You are a helpful assistant that answers questions based on the provided Notion documents.

            Instructions:
            1. Answer in Korean if the query is in Korean, otherwise answer in the same language as the query.
            2. Base your answer ONLY on the provided context from Notion documents.
            3. If the information is not in the context, say you don't have that information.
            4. Be concise but comprehensive.
            5. When referencing information, mention which document it comes from.
            6. Use markdown formatting when appropriate for better readability."""

            user_prompt = f"""Context from Notion documents:

{context}

---

Question: {query}

Please provide a comprehensive answer based on the above context."""

            # Call GPT API
            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model_chat,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            answer = response.choices[0].message.content
            return answer

        except Exception as e:
            logger.error("Failed to generate answer with GPT", error=str(e))
            raise

    def _format_sources(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format source documents for response.

        Args:
            documents: Retrieved documents.

        Returns:
            Formatted sources.
        """
        sources = []

        for doc in documents:
            metadata = doc.get("metadata", {})
            source = {
                "page_id": metadata.get("page_id", doc.get("id", "unknown")),
                "page_title": metadata.get("page_title", "Untitled"),
                "text": doc.get("text", "")[:500],  # Truncate for response
                "score": doc.get("score", 0.0),
                "url": metadata.get("url", ""),
                "chunk_index": metadata.get("chunk_index", 0),
                "total_chunks": metadata.get("total_chunks", 1)
            }
            sources.append(source)

        return sources

    async def get_similar_queries(
        self,
        query: str,
        limit: int = 5
    ) -> List[str]:
        """
        Get similar queries that have been asked before.

        This is a placeholder for future implementation where we
        store and analyze query history.

        Args:
            query: Current query.
            limit: Maximum number of similar queries to return.

        Returns:
            List of similar queries.
        """
        # TODO: Implement query history and similarity matching
        return []

    async def validate_configuration(self) -> Dict[str, bool]:
        """
        Validate RAG configuration and services.

        Returns:
            Validation status for each component.
        """
        status = {
            "openai_api": False,
            "vector_db": False,
            "embeddings": False
        }

        try:
            # Check OpenAI API
            status["openai_api"] = await self.embedding_service.validate_api_key()

            # Check vector DB
            if not self.vector_service.db:
                await self.vector_service.initialize()
            doc_count = await self.vector_service.count_documents()
            status["vector_db"] = True
            status["documents_indexed"] = doc_count > 0

            # Check embeddings
            test_embedding = await self.embedding_service.generate_embedding("test")
            status["embeddings"] = len(test_embedding) > 0

        except Exception as e:
            logger.error("Configuration validation failed", error=str(e))

        return status