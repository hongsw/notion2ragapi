"""OpenAI embedding generation service."""

from typing import List, Dict, Any, Optional
import openai
from openai import AsyncOpenAI
import numpy as np
import structlog
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = structlog.get_logger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""

    def __init__(self):
        """Initialize embedding service."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model_embedding
        self.max_batch_size = 100  # OpenAI recommended batch size

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to generate embedding for.

        Returns:
            Embedding vector as list of floats.
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            embedding = response.data[0].embedding
            logger.debug("Generated embedding", text_length=len(text))
            return embedding

        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e))
            raise

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to generate embeddings for.

        Returns:
            List of embedding vectors.
        """
        embeddings = []

        # Process in batches
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]

            try:
                response = await self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )

                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)

                logger.info("Generated embeddings batch",
                           batch_size=len(batch),
                           total_processed=len(embeddings),
                           total_texts=len(texts))

                # Small delay to avoid rate limiting
                if i + self.max_batch_size < len(texts):
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error("Failed to generate embeddings batch",
                            batch_index=i,
                            error=str(e))
                # For failed batches, try to process individually
                for text in batch:
                    try:
                        embedding = await self.generate_embedding(text)
                        embeddings.append(embedding)
                    except Exception as e2:
                        logger.error("Failed to generate individual embedding",
                                   error=str(e2))
                        # Append zero vector as fallback
                        embeddings.append([0.0] * 1536)  # Default dimension for ada-002

        return embeddings

    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        This is a specialized method for queries that might
        apply query-specific preprocessing.

        Args:
            query: Search query text.

        Returns:
            Query embedding vector.
        """
        # Could add query-specific preprocessing here
        query = query.strip()

        if not query:
            raise ValueError("Query cannot be empty")

        try:
            embedding = await self.generate_embedding(query)
            logger.info("Generated query embedding", query_length=len(query))
            return embedding

        except Exception as e:
            logger.error("Failed to generate query embedding",
                        query=query[:100],
                        error=str(e))
            raise

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector.
            vec2: Second vector.

        Returns:
            Cosine similarity score between -1 and 1.
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def find_similar(
        self,
        query_embedding: List[float],
        embeddings: List[Dict[str, Any]],
        top_k: int = 5,
        threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Find most similar embeddings to a query.

        Args:
            query_embedding: Query embedding vector.
            embeddings: List of dictionaries with 'embedding' and other metadata.
            top_k: Number of top results to return.
            threshold: Minimum similarity threshold.

        Returns:
            List of most similar items with similarity scores.
        """
        similarities = []

        for item in embeddings:
            similarity = self.cosine_similarity(
                query_embedding,
                item['embedding']
            )

            if similarity >= threshold:
                similarities.append({
                    **item,
                    'similarity': similarity
                })

        # Sort by similarity descending
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        # Return top k
        return similarities[:top_k]

    async def validate_api_key(self) -> bool:
        """
        Validate that the OpenAI API key is working.

        Returns:
            True if API key is valid, False otherwise.
        """
        try:
            # Try to generate a simple embedding
            await self.generate_embedding("test")
            logger.info("OpenAI API key validated successfully")
            return True
        except Exception as e:
            logger.error("OpenAI API key validation failed", error=str(e))
            return False

    def estimate_cost(self, num_tokens: int) -> float:
        """
        Estimate the cost of generating embeddings.

        Args:
            num_tokens: Total number of tokens to process.

        Returns:
            Estimated cost in USD.
        """
        # Pricing for text-embedding-3-small as of 2024
        # $0.02 per 1M tokens
        cost_per_million = 0.02

        estimated_cost = (num_tokens / 1_000_000) * cost_per_million
        return estimated_cost