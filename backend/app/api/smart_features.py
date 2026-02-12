"""
Smart Features API endpoints for FinRAG.

Provides AI-powered document intelligence:
- Smart question suggestions per document
- AI-generated executive summaries
- Financial metric extraction
- Multi-document comparison
"""

import logging
import json
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import StreamingResponse

from app.services.retrieval import RetrievalService, get_retrieval_service
from app.services.llm import LLMService, LLMServiceError, get_llm_service
from app.services.vector_store import VectorStore, get_vector_store
from app.middleware.auth import get_current_user, get_user_id, AuthenticatedUser
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api", tags=["Smart Features"])


# ═══════════════════════════════════════════════════════
# 1. SMART QUESTION SUGGESTIONS
# ═══════════════════════════════════════════════════════

SUGGESTIONS_PROMPT = """You are a financial document analyst. Based on the following content from a financial document, generate exactly 6 smart, specific questions that a retail investor would want to ask about this document.

The questions should:
- Be specific to the actual content (reference real figures, companies, dates if present)
- Cover different aspects: financial performance, risks, strategy, comparisons
- Range from simple factual to analytical
- Be concise (under 15 words each)

Document content sample:
{context}

Return ONLY a JSON array of 6 question strings. No explanation, just the JSON array.
Example format: ["Question 1?", "Question 2?", ...]"""


class SuggestionsResponse(BaseModel):
    """Response model for smart suggestions."""
    document_id: str
    suggestions: List[str]
    generated_from: str = "document_content"


@router.get(
    "/documents/{document_id}/suggestions",
    response_model=SuggestionsResponse,
    summary="Get Smart Question Suggestions",
    description="Auto-generate relevant questions based on document content."
)
async def get_suggestions(
    document_id: str,
    user_id: str = Depends(get_user_id),
    vector_store: VectorStore = Depends(get_vector_store),
    llm_service: LLMService = Depends(get_llm_service)
):
    """Generate smart question suggestions for a document."""
    try:
        # Get a representative sample of chunks from the document
        results = vector_store.search(
            user_id=user_id,
            query="key financial metrics revenue profit risk strategy overview",
            n_results=5,
            document_id=document_id
        )

        if not results or len(results.get("documents", [[]])[0]) == 0:
            # Return generic suggestions if no chunks found
            return SuggestionsResponse(
                document_id=document_id,
                suggestions=[
                    "What are the key financial highlights?",
                    "What is the total revenue reported?",
                    "What are the main risk factors?",
                    "How did the company perform this year?",
                    "What is the company's growth strategy?",
                    "Are there any significant changes from last year?"
                ],
                generated_from="default"
            )

        # Build context from retrieved chunks
        docs = results.get("documents", [[]])[0]
        context = "\n\n".join(docs[:5])[:3000]  # Cap at 3000 chars

        # Generate suggestions using LLM
        messages = [
            {"role": "system", "content": "You are a financial analysis assistant. Return only valid JSON."},
            {"role": "user", "content": SUGGESTIONS_PROMPT.format(context=context)}
        ]

        response = llm_service._call_openai(
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        # Parse the JSON response
        content = response["content"].strip()
        # Handle potential markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        suggestions = json.loads(content)

        if not isinstance(suggestions, list):
            raise ValueError("Expected a list")

        # Ensure we have exactly 6 suggestions
        suggestions = suggestions[:6]

        return SuggestionsResponse(
            document_id=document_id,
            suggestions=suggestions,
            generated_from="ai_analysis"
        )

    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse suggestions: {e}")
        return SuggestionsResponse(
            document_id=document_id,
            suggestions=[
                "What are the key financial highlights?",
                "What is the total revenue reported?",
                "What are the main risk factors?",
                "How did the company perform this year?",
                "What is the company's growth strategy?",
                "Are there any significant changes from last year?"
            ],
            generated_from="fallback"
        )
    except Exception as e:
        logger.error(f"Suggestions generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "error_code": "SUGGESTIONS_ERROR"}
        )


# ═══════════════════════════════════════════════════════
# 2. AI DOCUMENT SUMMARY
# ═══════════════════════════════════════════════════════

SUMMARY_PROMPT = """You are a senior financial analyst. Analyze the following content from a financial document and provide a structured executive summary.

Document content:
{context}

Provide your response in this exact JSON format:
{{
    "title": "Brief document title/description",
    "executive_summary": "2-3 sentence high-level overview",
    "key_takeaways": ["takeaway 1", "takeaway 2", "takeaway 3", "takeaway 4", "takeaway 5"],
    "financial_highlights": ["highlight 1", "highlight 2", "highlight 3"],
    "risk_factors": ["risk 1", "risk 2", "risk 3"],
    "bull_case": "1-2 sentence investment bull case",
    "bear_case": "1-2 sentence investment bear case",
    "sentiment": "positive" or "neutral" or "negative"
}}

Return ONLY valid JSON. No markdown, no explanation."""


class DocumentSummary(BaseModel):
    """AI-generated document summary."""
    document_id: str
    title: str
    executive_summary: str
    key_takeaways: List[str]
    financial_highlights: List[str]
    risk_factors: List[str]
    bull_case: str
    bear_case: str
    sentiment: str


@router.get(
    "/documents/{document_id}/summary",
    response_model=DocumentSummary,
    summary="Get AI Document Summary",
    description="Generate an executive summary with key takeaways, risk factors, and investment thesis."
)
async def get_document_summary(
    document_id: str,
    user_id: str = Depends(get_user_id),
    vector_store: VectorStore = Depends(get_vector_store),
    llm_service: LLMService = Depends(get_llm_service)
):
    """Generate an AI-powered executive summary of a document."""
    try:
        # Get comprehensive chunks from the document
        results = vector_store.search(
            user_id=user_id,
            query="executive summary financial results overview key metrics performance revenue profit loss risk factors strategy",
            n_results=8,
            document_id=document_id
        )

        docs = results.get("documents", [[]])[0] if results else []

        if not docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "No indexed content found for this document", "error_code": "NO_CONTENT"}
            )

        context = "\n\n".join(docs)[:5000]

        messages = [
            {"role": "system", "content": "You are a senior financial analyst. Return only valid JSON."},
            {"role": "user", "content": SUMMARY_PROMPT.format(context=context)}
        ]

        response = llm_service._call_openai(
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )

        content = response["content"].strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        summary_data = json.loads(content)

        return DocumentSummary(
            document_id=document_id,
            title=summary_data.get("title", "Financial Document"),
            executive_summary=summary_data.get("executive_summary", ""),
            key_takeaways=summary_data.get("key_takeaways", [])[:5],
            financial_highlights=summary_data.get("financial_highlights", [])[:3],
            risk_factors=summary_data.get("risk_factors", [])[:3],
            bull_case=summary_data.get("bull_case", ""),
            bear_case=summary_data.get("bear_case", ""),
            sentiment=summary_data.get("sentiment", "neutral")
        )

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error in summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "Failed to generate structured summary", "error_code": "PARSE_ERROR"}
        )
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "error_code": "SUMMARY_ERROR"}
        )


# ═══════════════════════════════════════════════════════
# 3. FINANCIAL METRICS EXTRACTION
# ═══════════════════════════════════════════════════════

FINANCIALS_PROMPT = """Extract key financial metrics from this document content. Look for revenue, net income, EPS, margins, debt, and any other key financial figures.

Document content:
{context}

Return ONLY a JSON object in this exact format:
{{
    "company_name": "Company Name",
    "period": "FY2024 or Q3 2024 etc.",
    "metrics": [
        {{"name": "Total Revenue", "value": "$XX.XB", "change": "+X.X%", "category": "income"}},
        {{"name": "Net Income", "value": "$X.XB", "change": "+X.X%", "category": "income"}},
        {{"name": "EPS", "value": "$X.XX", "change": "+X.X%", "category": "per_share"}},
        {{"name": "Operating Margin", "value": "XX.X%", "change": "+X.Xpp", "category": "margin"}},
        {{"name": "Total Debt", "value": "$X.XB", "change": "-X.X%", "category": "balance_sheet"}}
    ],
    "key_ratios": [
        {{"name": "P/E Ratio", "value": "XX.X"}},
        {{"name": "Debt/Equity", "value": "X.XX"}},
        {{"name": "ROE", "value": "XX.X%"}}
    ]
}}

Extract ONLY metrics that are explicitly stated in the document. If a metric is not found, omit it. Return ONLY valid JSON."""


class FinancialMetric(BaseModel):
    name: str
    value: str
    change: Optional[str] = None
    category: str = "other"


class KeyRatio(BaseModel):
    name: str
    value: str


class FinancialsResponse(BaseModel):
    document_id: str
    company_name: str
    period: str
    metrics: List[FinancialMetric]
    key_ratios: List[KeyRatio]


@router.get(
    "/documents/{document_id}/financials",
    response_model=FinancialsResponse,
    summary="Extract Financial Metrics",
    description="Auto-extract key financial metrics and ratios from the document."
)
async def get_financials(
    document_id: str,
    user_id: str = Depends(get_user_id),
    vector_store: VectorStore = Depends(get_vector_store),
    llm_service: LLMService = Depends(get_llm_service)
):
    """Extract financial metrics from a document."""
    try:
        # Search for financial data specifically
        results = vector_store.search(
            user_id=user_id,
            query="revenue net income earnings per share operating margin total debt equity ratio financial results",
            n_results=8,
            document_id=document_id
        )

        docs = results.get("documents", [[]])[0] if results else []

        if not docs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "No indexed content found", "error_code": "NO_CONTENT"}
            )

        context = "\n\n".join(docs)[:5000]

        messages = [
            {"role": "system", "content": "You are a financial data extraction expert. Return only valid JSON."},
            {"role": "user", "content": FINANCIALS_PROMPT.format(context=context)}
        ]

        response = llm_service._call_openai(
            messages=messages,
            temperature=0.1,
            max_tokens=1000
        )

        content = response["content"].strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        data = json.loads(content)

        metrics = [
            FinancialMetric(
                name=m.get("name", ""),
                value=m.get("value", ""),
                change=m.get("change"),
                category=m.get("category", "other")
            )
            for m in data.get("metrics", [])
        ]

        ratios = [
            KeyRatio(name=r.get("name", ""), value=r.get("value", ""))
            for r in data.get("key_ratios", [])
        ]

        return FinancialsResponse(
            document_id=document_id,
            company_name=data.get("company_name", "Unknown"),
            period=data.get("period", "Unknown"),
            metrics=metrics,
            key_ratios=ratios
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Financials extraction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "error_code": "FINANCIALS_ERROR"}
        )


# ═══════════════════════════════════════════════════════
# 4. MULTI-DOCUMENT COMPARISON
# ═══════════════════════════════════════════════════════

COMPARE_PROMPT = """You are a financial analyst comparing multiple documents. Based on the provided content from different documents, create a comprehensive comparison.

{documents_context}

Create a structured comparison. Return ONLY a JSON object:
{{
    "comparison_summary": "2-3 sentence overview of the comparison",
    "dimensions": [
        {{
            "dimension": "Revenue",
            "entries": [
                {{"document": "Doc 1 name", "value": "finding for doc 1"}},
                {{"document": "Doc 2 name", "value": "finding for doc 2"}}
            ],
            "insight": "Brief comparative insight"
        }}
    ],
    "overall_insight": "Key takeaway from the comparison"
}}"""


class CompareRequest(BaseModel):
    document_ids: List[str] = Field(..., min_length=2, max_length=5)
    question: Optional[str] = Field(None, description="Optional comparison question")


class ComparisonEntry(BaseModel):
    document: str
    value: str


class ComparisonDimension(BaseModel):
    dimension: str
    entries: List[ComparisonEntry]
    insight: str


class CompareResponse(BaseModel):
    comparison_summary: str
    dimensions: List[ComparisonDimension]
    overall_insight: str
    documents_compared: List[str]


@router.post(
    "/compare",
    response_model=CompareResponse,
    summary="Compare Multiple Documents",
    description="Generate a side-by-side comparison of financial documents."
)
async def compare_documents(
    request: CompareRequest,
    user_id: str = Depends(get_user_id),
    vector_store: VectorStore = Depends(get_vector_store),
    llm_service: LLMService = Depends(get_llm_service)
):
    """Compare multiple documents side by side."""
    try:
        query = request.question or "key financial metrics revenue profit strategy risk performance"

        documents_context = ""
        doc_names = []

        for i, doc_id in enumerate(request.document_ids):
            results = vector_store.search(
                user_id=user_id,
                query=query,
                n_results=4,
                document_id=doc_id
            )

            docs = results.get("documents", [[]])[0] if results else []
            metadatas = results.get("metadatas", [[]])[0] if results else []

            # Try to get document name from metadata
            doc_name = f"Document {i+1}"
            if metadatas:
                doc_name = metadatas[0].get("filename", metadatas[0].get("document_id", doc_name))
            doc_names.append(doc_name)

            content = "\n".join(docs)[:2000]
            documents_context += f"\n--- {doc_name} ---\n{content}\n"

        messages = [
            {"role": "system", "content": "You are a financial analyst. Return only valid JSON."},
            {"role": "user", "content": COMPARE_PROMPT.format(documents_context=documents_context)}
        ]

        response = llm_service._call_openai(
            messages=messages,
            temperature=0.3,
            max_tokens=1500
        )

        content = response["content"].strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        data = json.loads(content)

        dimensions = [
            ComparisonDimension(
                dimension=d.get("dimension", ""),
                entries=[ComparisonEntry(**e) for e in d.get("entries", [])],
                insight=d.get("insight", "")
            )
            for d in data.get("dimensions", [])
        ]

        return CompareResponse(
            comparison_summary=data.get("comparison_summary", ""),
            dimensions=dimensions,
            overall_insight=data.get("overall_insight", ""),
            documents_compared=doc_names
        )

    except Exception as e:
        logger.error(f"Document comparison failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "error_code": "COMPARE_ERROR"}
        )


# ═══════════════════════════════════════════════════════
# 5. STREAMING CHAT (SSE)
# ═══════════════════════════════════════════════════════

class StreamRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    document_id: Optional[str] = None
    n_chunks: int = Field(5, ge=1, le=10)


@router.post(
    "/chat/stream",
    summary="Streaming Chat with Documents",
    description="Stream AI responses token-by-token using Server-Sent Events."
)
async def stream_chat(
    request: StreamRequest,
    user_id: str = Depends(get_user_id),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    """Stream chat responses using SSE."""
    # Step 1: Retrieve context (non-streaming)
    retrieval_result = retrieval_service.retrieve_and_format(
        user_id=user_id,
        query=request.question,
        n_results=request.n_chunks,
        document_id=request.document_id
    )

    if retrieval_result["num_chunks"] == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "No relevant documents found", "error_code": "NO_DOCUMENTS"}
        )

    context = retrieval_result["context"]
    chunks = retrieval_result["chunks"]
    sources = []
    for c in chunks:
        meta = c.get("metadata", {})
        sources.append({
            "page_number": meta.get("page_number", 0),
            "chunk_type": meta.get("chunk_type", "text"),
            "section_header": meta.get("section_header"),
            "content_preview": c.get("content", "")[:150]
        })

    # Step 2: Stream LLM response
    async def generate():
        try:
            # Send sources first
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

            # Build prompt
            messages = llm_service.build_prompt(context, request.question)

            # Stream from LLM
            stream = llm_service.client.chat.completions.create(
                model=llm_service.model,
                messages=messages,
                temperature=0.1,
                max_tokens=1000,
                stream=True
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ═══════════════════════════════════════════════════════
# 6. CONVERSATION MEMORY
# ═══════════════════════════════════════════════════════

# In-memory conversation store (per user per document)
_conversation_store: Dict[str, List[Dict[str, str]]] = {}


class ConversationRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    document_id: Optional[str] = None
    session_id: Optional[str] = None
    n_chunks: int = Field(5, ge=1, le=10)


class ConversationResponse(BaseModel):
    answer: str
    question: str
    session_id: str
    sources: List[Dict[str, Any]]
    history_length: int


@router.post(
    "/chat/conversation",
    response_model=ConversationResponse,
    summary="Chat with Conversation Memory",
    description="Chat with documents while maintaining conversation history for follow-up questions."
)
async def conversation_chat(
    request: ConversationRequest,
    user_id: str = Depends(get_user_id),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    """Chat with conversation memory."""
    try:
        # Generate session ID if not provided
        session_id = request.session_id or f"{user_id}_{request.document_id or 'all'}"

        # Get conversation history
        history = _conversation_store.get(session_id, [])

        # Retrieve context
        retrieval_result = retrieval_service.retrieve_and_format(
            user_id=user_id,
            query=request.question,
            n_results=request.n_chunks,
            document_id=request.document_id
        )

        context = retrieval_result.get("context", "")
        chunks = retrieval_result.get("chunks", [])

        # Build conversation-aware prompt
        conversation_context = ""
        if history:
            conversation_context = "\n\nPrevious conversation:\n"
            for msg in history[-6:]:  # Keep last 3 exchanges
                conversation_context += f"User: {msg['user']}\nAssistant: {msg['assistant']}\n\n"

        system_prompt = f"""You are a financial document QA assistant with memory of the conversation.
Answer based on the provided context. If referencing previous conversation, make it clear.
If the user asks a follow-up question, use the conversation history for context.

Guidelines:
- Answer based ONLY on the provided document context
- Reference previous answers when relevant
- Cite page numbers and sections
- Be precise with financial figures{conversation_context}"""

        user_prompt = f"""Context from the financial document:
{context}

---

Question: {request.question}

Provide a clear answer based on the context. If this is a follow-up question, reference the previous conversation."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = llm_service._call_openai(
            messages=messages,
            temperature=0.1,
            max_tokens=1000
        )

        answer = response["content"]

        # Store in conversation history
        history.append({
            "user": request.question,
            "assistant": answer
        })
        _conversation_store[session_id] = history[-10:]  # Keep last 10 exchanges

        # Extract sources
        sources = []
        for c in chunks:
            meta = c.get("metadata", {})
            sources.append({
                "page_number": meta.get("page_number", 0),
                "chunk_type": meta.get("chunk_type", "text"),
                "section_header": meta.get("section_header"),
                "content_preview": c.get("content", "")[:150]
            })

        return ConversationResponse(
            answer=answer,
            question=request.question,
            session_id=session_id,
            sources=sources,
            history_length=len(history)
        )

    except Exception as e:
        logger.error(f"Conversation chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "error_code": "CONVERSATION_ERROR"}
        )


@router.delete(
    "/chat/conversation/{session_id}",
    summary="Clear Conversation History",
    description="Reset conversation memory for a session."
)
async def clear_conversation(
    session_id: str,
    user_id: str = Depends(get_user_id)
):
    """Clear conversation history for a session."""
    key = session_id
    if key in _conversation_store:
        del _conversation_store[key]
    return {"status": "cleared", "session_id": session_id}


# ═══════════════════════════════════════════════════════
# 7. RAG ANALYTICS
# ═══════════════════════════════════════════════════════

# In-memory analytics store
_analytics_store: Dict[str, Any] = {
    "total_queries": 0,
    "total_documents": 0,
    "total_tokens_used": 0,
    "queries_by_day": {},
    "popular_topics": {},
    "avg_confidence": [],
    "response_times": []
}


def track_query(user_id: str, question: str, tokens: int, response_time: float, confidence: float):
    """Track a query for analytics."""
    from datetime import datetime
    _analytics_store["total_queries"] += 1
    _analytics_store["total_tokens_used"] += tokens

    today = datetime.now().strftime("%Y-%m-%d")
    _analytics_store["queries_by_day"][today] = _analytics_store["queries_by_day"].get(today, 0) + 1

    # Track topic keywords
    words = question.lower().split()
    for word in words:
        if len(word) > 4:
            _analytics_store["popular_topics"][word] = _analytics_store["popular_topics"].get(word, 0) + 1

    _analytics_store["avg_confidence"].append(confidence)
    _analytics_store["response_times"].append(response_time)

    # Keep only last 100 entries
    _analytics_store["avg_confidence"] = _analytics_store["avg_confidence"][-100:]
    _analytics_store["response_times"] = _analytics_store["response_times"][-100:]


class AnalyticsResponse(BaseModel):
    total_queries: int
    total_documents: int
    total_tokens_used: int
    avg_confidence: float
    avg_response_time: float
    queries_by_day: Dict[str, int]
    popular_topics: List[Dict[str, Any]]


@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    summary="Get RAG Analytics",
    description="Get usage analytics including query counts, token usage, and popular topics."
)
async def get_analytics(
    user_id: str = Depends(get_user_id),
    vector_store: VectorStore = Depends(get_vector_store)
):
    """Get RAG analytics dashboard data."""
    try:
        # Get document count
        stats = vector_store.get_collection_stats(user_id)
        doc_count = stats.get("total_chunks", 0)

        # Calculate averages
        avg_conf = sum(_analytics_store["avg_confidence"]) / len(_analytics_store["avg_confidence"]) if _analytics_store["avg_confidence"] else 0.0
        avg_time = sum(_analytics_store["response_times"]) / len(_analytics_store["response_times"]) if _analytics_store["response_times"] else 0.0

        # Get top topics
        topics = sorted(
            _analytics_store["popular_topics"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return AnalyticsResponse(
            total_queries=_analytics_store["total_queries"],
            total_documents=doc_count,
            total_tokens_used=_analytics_store["total_tokens_used"],
            avg_confidence=round(avg_conf, 3),
            avg_response_time=round(avg_time, 2),
            queries_by_day=dict(list(_analytics_store["queries_by_day"].items())[-7:]),
            popular_topics=[{"topic": t[0], "count": t[1]} for t in topics]
        )

    except Exception as e:
        logger.error(f"Analytics fetch failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": str(e), "error_code": "ANALYTICS_ERROR"}
        )
