"""
Answer Generation API endpoint for FinRAG.

Combines retrieval and LLM to provide complete answers
to user questions about financial documents.
"""

import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, status, Depends

from app.services.retrieval import RetrievalService, get_retrieval_service
from app.services.llm import LLMService, LLMServiceError, get_llm_service
from app.middleware.auth import get_current_user, get_user_id, AuthenticatedUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Answer"])


class AnswerRequest(BaseModel):
    """Request model for answer generation."""
    question: str = Field(
        ..., 
        description="The question to answer",
        min_length=1,
        max_length=1000
    )
    # user_id is extracted from auth token
    document_id: Optional[str] = Field(
        None, 
        description="Optional: Filter to specific document"
    )
    n_chunks: int = Field(
        5, 
        description="Number of chunks to retrieve",
        ge=1, 
        le=10
    )
    use_reranking: bool = Field(
        True, 
        description="Whether to use cross-encoder reranking"
    )
    temperature: float = Field(
        0.1,
        description="LLM temperature (0-1, lower = more focused)",
        ge=0,
        le=1
    )


class SourceInfo(BaseModel):
    """Source citation information."""
    page_number: int
    chunk_type: str
    section_header: Optional[str]
    content_preview: str


class ChunkInfo(BaseModel):
    """Information about a used chunk."""
    chunk_id: Optional[str]
    page: Optional[int]
    type: Optional[str]
    similarity_score: Optional[float]
    rerank_score: Optional[float]


class UsageInfo(BaseModel):
    """Token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class AnswerResponse(BaseModel):
    """Response model for answer generation."""
    answer: str
    question: str
    sources: List[SourceInfo]
    chunks_used: List[ChunkInfo]
    model: str
    usage: UsageInfo
    document_id: Optional[str]


@router.post(
    "/answer",
    response_model=AnswerResponse,
    summary="Get Answer to Question",
    description="""
    Ask a question about your indexed financial documents and receive an AI-generated answer.
    
    This endpoint:
    1. Retrieves the most relevant chunks from your documents
    2. Reranks them using a cross-encoder (optional)
    3. Sends the context to GPT-4 with a specialized prompt
    4. Returns the answer with source citations
    
    The answer will include:
    - The generated answer text
    - Source citations (page numbers, sections)
    - Information about which chunks were used
    - Token usage statistics
    """,
    responses={
        200: {"description": "Answer generated successfully"},
        400: {"description": "Invalid request"},
        404: {"description": "No relevant documents found"},
        422: {"description": "Answer generation failed"},
        500: {"description": "Internal server error"},
    }
)
async def generate_answer(
    request: AnswerRequest,
    user_id: str = Depends(get_user_id),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Generate an answer to a question using RAG.
    
    Args:
        request: Answer request with question and parameters
        retrieval_service: Service for retrieving relevant chunks
        llm_service: Service for generating answers with GPT-4
        
    Returns:
        AnswerResponse with the generated answer and metadata
    """
    try:
        # Configure reranking
        retrieval_service.use_reranking = request.use_reranking
        
        # Step 1: Retrieve relevant chunks
        logger.info(f"Retrieving chunks for question: '{request.question[:50]}...'")
        
        retrieval_result = retrieval_service.retrieve_and_format(
            user_id=user_id,
            query=request.question,
            n_results=request.n_chunks,
            document_id=request.document_id
        )
        
        if retrieval_result["num_chunks"] == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "No relevant documents found. Please make sure documents are uploaded and indexed.",
                    "error_code": "NO_DOCUMENTS"
                }
            )
        
        chunks = retrieval_result["chunks"]
        context = retrieval_result["context"]
        
        logger.info(f"Retrieved {len(chunks)} chunks")
        
        # Step 2: Generate answer using LLM
        logger.info("Generating answer with GPT-4...")
        
        try:
            answer_result = llm_service.answer_question(
                question=request.question,
                context=context,
                chunks=chunks
            )
        except LLMServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": e.message,
                    "error_code": e.error_code,
                    "retryable": e.retryable
                }
            )
        
        # Step 3: Format response
        sources = [
            SourceInfo(
                page_number=s["page_number"],
                chunk_type=s["chunk_type"],
                section_header=s.get("section_header"),
                content_preview=s["content_preview"]
            )
            for s in answer_result["sources"]
        ]
        
        chunks_info = [
            ChunkInfo(
                chunk_id=c.get("chunk_id"),
                page=c.get("page"),
                type=c.get("type"),
                similarity_score=c.get("similarity_score"),
                rerank_score=c.get("rerank_score")
            )
            for c in answer_result["chunks_used"]
        ]
        
        usage = UsageInfo(
            prompt_tokens=answer_result["usage"]["prompt_tokens"],
            completion_tokens=answer_result["usage"]["completion_tokens"],
            total_tokens=answer_result["usage"]["total_tokens"]
        )
        
        logger.info(
            f"Answer generated successfully. "
            f"Tokens: {usage.total_tokens}"
        )
        
        return AnswerResponse(
            answer=answer_result["answer"],
            question=request.question,
            sources=sources,
            chunks_used=chunks_info,
            model=answer_result["model"],
            usage=usage,
            document_id=request.document_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in answer generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "An unexpected error occurred while generating the answer",
                "error_code": "ANSWER_ERROR",
                "details": str(e)
            }
        )


@router.post(
    "/chat",
    summary="Chat with Documents (Simplified)",
    description="""
    A simplified chat endpoint that returns just the answer.
    
    Use this for a cleaner chat-like experience without all the metadata.
    """
)
async def chat_with_documents(
    request: AnswerRequest,
    user_id: str = Depends(get_user_id),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Simplified chat endpoint.
    
    Returns just the answer and basic source info.
    """
    # Reuse the answer generation logic
    response = await generate_answer(request, user_id, retrieval_service, llm_service)
    
    # Return simplified response
    return {
        "question": response.question,
        "answer": response.answer,
        "sources": [
            f"Page {s.page_number}" + (f" ({s.section_header})" if s.section_header else "")
            for s in response.sources
        ],
        "tokens_used": response.usage.total_tokens
    }
