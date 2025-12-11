"""Query API endpoints."""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import structlog

from app.services.rag_service import RAGService
from app.api.auth import verify_api_key

router = APIRouter()
logger = structlog.get_logger(__name__)


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str = Field(..., min_length=1, max_length=1000,
                      description="Natural language query")
    top_k: Optional[int] = Field(5, ge=1, le=20,
                                 description="Number of relevant documents to retrieve")
    temperature: Optional[float] = Field(0.7, ge=0, le=2,
                                        description="LLM temperature for response generation")


class Source(BaseModel):
    """Source document model."""
    page_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = {}


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    answer: str
    sources: List[Source]
    query: str
    model_used: str = "gpt-4-turbo-preview"


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: Request,
    query_request: QueryRequest,
    api_key: str = Depends(verify_api_key)
) -> QueryResponse:
    """
    Query indexed Notion documents using natural language.

    This endpoint:
    1. Takes a natural language query
    2. Searches for relevant document chunks using vector similarity
    3. Generates an answer using GPT-4 with the retrieved context
    4. Returns the answer along with source documents
    """
    try:
        logger.info("Processing query",
                   query=query_request.query[:100],
                   top_k=query_request.top_k)

        # Get RAG service from app state
        if not hasattr(request.app.state, "rag_service"):
            # Initialize RAG service if not exists
            request.app.state.rag_service = RAGService()

        rag_service = request.app.state.rag_service

        # Perform RAG query
        result = await rag_service.query(
            query=query_request.query,
            top_k=query_request.top_k,
            temperature=query_request.temperature
        )

        # Format sources
        sources = [
            Source(
                page_id=doc.get("page_id", "unknown"),
                text=doc.get("text", ""),
                score=doc.get("score", 0.0),
                metadata=doc.get("metadata", {})
            )
            for doc in result.get("sources", [])
        ]

        response = QueryResponse(
            answer=result.get("answer", "I couldn't find relevant information to answer your question."),
            sources=sources,
            query=query_request.query,
            model_used=result.get("model_used", "gpt-4-turbo-preview")
        )

        logger.info("Query processed successfully",
                   num_sources=len(sources))

        return response

    except Exception as e:
        logger.error("Query processing failed",
                    error=str(e),
                    query=query_request.query[:100])
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/query/history")
async def get_query_history(
    limit: int = 10,
    offset: int = 0,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    Get query history.

    Returns recent queries and their results.
    """
    # TODO: Implement query history retrieval from database
    return {
        "history": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }