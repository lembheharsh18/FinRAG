"""
LLM Service for FinRAG.

Handles LLM interactions for answer generation
in the RAG pipeline. Supports Groq (preferred) and OpenAI.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from openai import OpenAI, APIError, RateLimitError, APIConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# Prompt Templates
SYSTEM_PROMPT = """You are a financial document QA assistant for retail investors. Your role is to help users understand financial documents accurately and clearly.

Guidelines:
- Answer questions based ONLY on the provided context from the financial documents
- If the answer is not in the context, clearly state: "I cannot find this information in the provided document."
- Always cite which section, page, or source the information comes from (e.g., "According to Page 5..." or "As stated in the Income Statement section...")
- When referencing tables, mention it explicitly (e.g., "The table on Page 3 shows...")
- Be precise with financial figures - do not round or estimate unless explicitly stated
- If multiple sources contain relevant information, synthesize them and cite all sources
- Use clear, professional language appropriate for retail investors
- If you're uncertain about something, indicate the level of confidence"""

USER_PROMPT_TEMPLATE = """Context from the financial document:
{context}

---

Question: {question}

Please provide a clear, accurate answer based on the context above. Include specific citations to the source material."""


@dataclass
class AnswerSource:
    """A source citation for an answer."""
    page_number: int
    chunk_type: str
    section_header: Optional[str]
    content_preview: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_number": self.page_number,
            "chunk_type": self.chunk_type,
            "section_header": self.section_header,
            "content_preview": self.content_preview
        }


@dataclass 
class GeneratedAnswer:
    """A generated answer with metadata."""
    answer: str
    sources: List[AnswerSource]
    chunks_used: List[Dict[str, Any]]
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "sources": [s.to_dict() for s in self.sources],
            "chunks_used": self.chunks_used,
            "model": self.model,
            "usage": {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens
            }
        }


class LLMServiceError(Exception):
    """Custom exception for LLM service errors."""
    def __init__(self, message: str, error_code: str = "LLM_ERROR", retryable: bool = False):
        self.message = message
        self.error_code = error_code
        self.retryable = retryable
        super().__init__(self.message)


class LLMService:
    """
    LLM service for answer generation.
    
    Supports Groq (preferred, free) and OpenAI backends.
    Both use the OpenAI-compatible SDK.
    """
    
    def __init__(self):
        """Initialize the LLM client (Groq preferred, OpenAI fallback)."""
        # Prefer Groq (free, fast)
        if settings.groq_api_key:
            base_url = settings.llm_base_url or "https://api.groq.com/openai/v1"
            self.client = OpenAI(
                api_key=settings.groq_api_key,
                base_url=base_url
            )
            self.model = settings.groq_model
            self.provider = "groq"
            logger.info(f"LLM Service initialized with Groq model: {self.model}")
        elif settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_model
            self.provider = "openai"
            logger.info(f"LLM Service initialized with OpenAI model: {self.model}")
        else:
            raise LLMServiceError(
                "No LLM API key configured. Set GROQ_API_KEY or OPENAI_API_KEY in .env",
                "API_KEY_MISSING"
            )
    
    def build_prompt(
        self,
        context: str,
        question: str
    ) -> List[Dict[str, str]]:
        """
        Build the message prompt for GPT-4.
        
        Args:
            context: Formatted context from retrieved chunks
            question: User's question
            
        Returns:
            List of message dictionaries for the API
        """
        user_prompt = USER_PROMPT_TEMPLATE.format(
            context=context,
            question=question
        )
        
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APIConnectionError))
    )
    def _call_openai(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Call the OpenAI API with retry logic.
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature (lower = more focused)
            max_tokens: Maximum tokens in response
            
        Returns:
            API response dictionary
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except RateLimitError as e:
            logger.warning(f"Rate limit hit: {e}")
            raise  # Will be retried
            
        except APIConnectionError as e:
            logger.warning(f"Connection error: {e}")
            raise  # Will be retried
            
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise LLMServiceError(
                f"OpenAI API error: {str(e)}",
                "API_ERROR",
                retryable=False
            )
    
    def _extract_sources(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[AnswerSource]:
        """
        Extract source citations from chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of AnswerSource objects
        """
        sources = []
        
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            content = chunk.get("content", "")
            
            source = AnswerSource(
                page_number=metadata.get("page_number", 0),
                chunk_type=metadata.get("chunk_type", "text"),
                section_header=metadata.get("section_header"),
                content_preview=content[:150] + "..." if len(content) > 150 else content
            )
            sources.append(source)
        
        return sources
    
    def generate_answer(
        self,
        context: str,
        question: str,
        chunks: List[Dict[str, Any]],
        temperature: float = 0.1,
        max_tokens: int = 1000
    ) -> GeneratedAnswer:
        """
        Generate an answer using GPT-4.
        
        Args:
            context: Formatted context string
            question: User's question
            chunks: List of retrieved chunks with metadata
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            GeneratedAnswer with answer, sources, and usage info
        """
        logger.info(f"Generating answer for: '{question[:50]}...'")
        
        # Build the prompt
        messages = self.build_prompt(context, question)
        
        # Call OpenAI
        try:
            response = self._call_openai(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except LLMServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            raise LLMServiceError(
                f"Failed to generate answer: {str(e)}",
                "GENERATION_ERROR"
            )
        
        # Extract sources from chunks
        sources = self._extract_sources(chunks)
        
        # Prepare chunks_used (simplified version for response)
        chunks_used = [
            {
                "chunk_id": c.get("chunk_id"),
                "page": c.get("metadata", {}).get("page_number"),
                "type": c.get("metadata", {}).get("chunk_type"),
                "similarity_score": c.get("similarity_score"),
                "rerank_score": c.get("rerank_score")
            }
            for c in chunks
        ]
        
        answer = GeneratedAnswer(
            answer=response["content"],
            sources=sources,
            chunks_used=chunks_used,
            model=response["model"],
            prompt_tokens=response["prompt_tokens"],
            completion_tokens=response["completion_tokens"],
            total_tokens=response["total_tokens"]
        )
        
        logger.info(
            f"Answer generated. Tokens used: {answer.total_tokens} "
            f"(prompt: {answer.prompt_tokens}, completion: {answer.completion_tokens})"
        )
        
        return answer
    
    def answer_question(
        self,
        question: str,
        context: str,
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        High-level method to answer a question.
        
        Args:
            question: User's question
            context: Formatted context
            chunks: Retrieved chunks
            
        Returns:
            Dictionary with answer and metadata
        """
        answer = self.generate_answer(
            context=context,
            question=question,
            chunks=chunks
        )
        
        return answer.to_dict()


def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    return LLMService()
