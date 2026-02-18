"""
RAG vs LLM Evaluation API endpoints for FinRAG.

Provides side-by-side comparison of RAG-grounded answers
vs LLM-only answers, with faithfulness scoring.
"""

import time
import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.services.retrieval import RetrievalService, get_retrieval_service
from app.services.llm import LLMService, get_llm_service
from app.config import get_settings
from app.middleware.auth import get_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/evaluate", tags=["Evaluation"])
settings = get_settings()

# In-memory evaluation store
_evaluation_history: List[Dict[str, Any]] = []


# ── Prompts ───────────────────────────────────────────

FAITHFULNESS_JUDGE_PROMPT = """You are an evaluation judge. Given a CONTEXT, a QUESTION, and an ANSWER, rate how faithful the answer is to the context.

Faithfulness means: every claim in the answer is supported by the context. 

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
{answer}

Rate the faithfulness on a scale of 0.0 to 1.0 where:
- 1.0 = Every claim is directly supported by the context
- 0.7 = Most claims are supported, minor extrapolations
- 0.5 = Some claims are supported, some are not
- 0.3 = Few claims are supported by the context
- 0.0 = The answer contradicts or is unrelated to the context

Return ONLY a JSON object:
{{"score": <float>, "reasoning": "<brief explanation>"}}
"""

LLM_ONLY_PROMPT = """You are a financial analyst. Answer the following question based on your general knowledge. Be specific and provide numbers if you can.

Question: {question}

Provide a clear, concise answer."""


# ── Models ────────────────────────────────────────────

class CompareRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    document_id: Optional[str] = None
    n_chunks: int = Field(5, ge=1, le=10)


class SourceInfo(BaseModel):
    page_number: int
    chunk_type: str
    section_header: Optional[str] = None
    content_preview: str


class EvaluationResult(BaseModel):
    question: str
    rag_answer: str
    rag_sources: List[SourceInfo]
    rag_faithfulness: float
    rag_reasoning: str
    llm_answer: str
    llm_faithfulness: float
    llm_reasoning: str
    rag_response_time: float
    llm_response_time: float
    winner: str
    document_id: Optional[str] = None
    timestamp: str


class EvaluationReport(BaseModel):
    total_evaluations: int
    avg_rag_faithfulness: float
    avg_llm_faithfulness: float
    rag_win_rate: float
    avg_rag_response_time: float
    avg_llm_response_time: float
    recent_evaluations: List[Dict[str, Any]]


# ── Endpoints ─────────────────────────────────────────

@router.post(
    "/compare",
    response_model=EvaluationResult,
    summary="Compare RAG vs LLM",
    description="""
    Generate both a RAG-grounded answer and an LLM-only answer for the same question.
    Returns both answers with faithfulness scores for comparison.
    """
)
async def compare_rag_vs_llm(
    request: CompareRequest,
    user_id: str = Depends(get_user_id),
    retrieval_service: RetrievalService = Depends(get_retrieval_service),
    llm_service: LLMService = Depends(get_llm_service)
):
    """Compare RAG answer vs LLM-only answer with faithfulness scoring."""
    try:
        # 1. Get RAG answer
        rag_start = time.time()
        
        retrieval_result = retrieval_service.retrieve_and_format(
            user_id=user_id,
            query=request.question,
            n_results=request.n_chunks,
            document_id=request.document_id
        )
        
        context = retrieval_result["context"]
        chunks = retrieval_result["chunks"]
        
        rag_generated = llm_service.generate_answer(
            context=context,
            question=request.question,
            chunks=chunks
        )
        rag_answer = rag_generated.answer
        rag_time = time.time() - rag_start
        
        # Extract sources
        rag_sources = []
        for src in rag_generated.sources:
            rag_sources.append(SourceInfo(
                page_number=src.page_number,
                chunk_type=src.chunk_type,
                section_header=src.section_header,
                content_preview=src.content_preview[:150]
            ))

        # 2. Get LLM-only answer (no context)
        llm_start = time.time()
        
        llm_messages = [
            {"role": "system", "content": "You are a helpful financial analyst."},
            {"role": "user", "content": LLM_ONLY_PROMPT.format(question=request.question)}
        ]
        
        llm_response = llm_service._call_openai(llm_messages, temperature=0.3, max_tokens=800)
        llm_answer = llm_response.choices[0].message.content.strip()
        llm_time = time.time() - llm_start

        # 3. Judge faithfulness of RAG answer
        rag_faith_prompt = FAITHFULNESS_JUDGE_PROMPT.format(
            context=context[:3000],
            question=request.question,
            answer=rag_answer
        )
        rag_judge_msgs = [
            {"role": "system", "content": "You are an evaluation judge. Return only valid JSON."},
            {"role": "user", "content": rag_faith_prompt}
        ]
        rag_judge_resp = llm_service._call_openai(rag_judge_msgs, temperature=0.0, max_tokens=200)
        rag_judge_text = rag_judge_resp.choices[0].message.content.strip()
        
        try:
            # Try to parse JSON, handle markdown fencing
            clean = rag_judge_text.replace("```json", "").replace("```", "").strip()
            rag_judge = json.loads(clean)
            rag_faithfulness = float(rag_judge.get("score", 0.5))
            rag_reasoning = rag_judge.get("reasoning", "")
        except (json.JSONDecodeError, ValueError):
            rag_faithfulness = 0.5
            rag_reasoning = "Could not parse judge response"

        # 4. Judge faithfulness of LLM-only answer against same context
        llm_faith_prompt = FAITHFULNESS_JUDGE_PROMPT.format(
            context=context[:3000],
            question=request.question,
            answer=llm_answer
        )
        llm_judge_msgs = [
            {"role": "system", "content": "You are an evaluation judge. Return only valid JSON."},
            {"role": "user", "content": llm_faith_prompt}
        ]
        llm_judge_resp = llm_service._call_openai(llm_judge_msgs, temperature=0.0, max_tokens=200)
        llm_judge_text = llm_judge_resp.choices[0].message.content.strip()
        
        try:
            clean = llm_judge_text.replace("```json", "").replace("```", "").strip()
            llm_judge = json.loads(clean)
            llm_faithfulness = float(llm_judge.get("score", 0.3))
            llm_reasoning = llm_judge.get("reasoning", "")
        except (json.JSONDecodeError, ValueError):
            llm_faithfulness = 0.3
            llm_reasoning = "Could not parse judge response"

        # 5. Determine winner
        winner = "rag" if rag_faithfulness >= llm_faithfulness else "llm"

        result = EvaluationResult(
            question=request.question,
            rag_answer=rag_answer,
            rag_sources=rag_sources,
            rag_faithfulness=rag_faithfulness,
            rag_reasoning=rag_reasoning,
            llm_answer=llm_answer,
            llm_faithfulness=llm_faithfulness,
            llm_reasoning=llm_reasoning,
            rag_response_time=round(rag_time, 2),
            llm_response_time=round(llm_time, 2),
            winner=winner,
            document_id=request.document_id,
            timestamp=datetime.utcnow().isoformat()
        )

        # Store evaluation
        _evaluation_history.append(result.model_dump())
        
        logger.info(f"Evaluation: RAG={rag_faithfulness:.2f} vs LLM={llm_faithfulness:.2f} → {winner}")
        return result

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Evaluation failed", "details": str(e)}
        )


@router.get(
    "/report",
    response_model=EvaluationReport,
    summary="Evaluation Report",
    description="Get aggregate evaluation metrics."
)
async def get_report(user_id: str = Depends(get_user_id)):
    """Get aggregate evaluation report."""
    total = len(_evaluation_history)
    
    if total == 0:
        return EvaluationReport(
            total_evaluations=0,
            avg_rag_faithfulness=0.0,
            avg_llm_faithfulness=0.0,
            rag_win_rate=0.0,
            avg_rag_response_time=0.0,
            avg_llm_response_time=0.0,
            recent_evaluations=[]
        )
    
    avg_rag = sum(e["rag_faithfulness"] for e in _evaluation_history) / total
    avg_llm = sum(e["llm_faithfulness"] for e in _evaluation_history) / total
    rag_wins = sum(1 for e in _evaluation_history if e["winner"] == "rag")
    avg_rag_time = sum(e["rag_response_time"] for e in _evaluation_history) / total
    avg_llm_time = sum(e["llm_response_time"] for e in _evaluation_history) / total
    
    recent = _evaluation_history[-10:][::-1]  # Last 10, newest first
    
    return EvaluationReport(
        total_evaluations=total,
        avg_rag_faithfulness=round(avg_rag, 3),
        avg_llm_faithfulness=round(avg_llm, 3),
        rag_win_rate=round(rag_wins / total, 3),
        avg_rag_response_time=round(avg_rag_time, 2),
        avg_llm_response_time=round(avg_llm_time, 2),
        recent_evaluations=recent
    )
