"""
Chat router for conversational query operations using LangChain agent.
"""

import logging
import os
import asyncio
import time
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List

from ..services.database import get_db
from ..agent import FeedbackAnalysisAgent

logger = logging.getLogger(__name__)

# Global agent instance - in production, you'd want better lifecycle management
_agent_instance: Optional[FeedbackAnalysisAgent] = None
_agent_lock = asyncio.Lock()  # Thread-safe agent initialization

async def get_feedback_agent() -> FeedbackAnalysisAgent:
    """Get or create the feedback analysis agent instance with thread safety."""
    global _agent_instance

    # Fast path - agent already initialized
    if _agent_instance is not None:
        return _agent_instance

    # Slow path - initialize with lock
    async with _agent_lock:
        # Double-check pattern
        if _agent_instance is not None:
            return _agent_instance

        try:
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")

            # Initialize agent in thread pool to avoid blocking
            _agent_instance = await asyncio.get_event_loop().run_in_executor(
                None, FeedbackAnalysisAgent, openai_api_key
            )
            logger.info("FeedbackAnalysisAgent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize FeedbackAnalysisAgent: {e}")
            raise

    return _agent_instance

router = APIRouter()

# Filters for query requests
class DateRangeFilter(BaseModel):
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")

class QueryFilters(BaseModel):
    date_range: Optional[DateRangeFilter] = Field(None, description="Date range filter")
    sentiment: Optional[int] = Field(None, description="Sentiment filter: -1 (negative), 0 (neutral), 1 (positive)")
    topic_ids: Optional[List[int]] = Field(None, description="List of topic IDs to filter by")
    source: Optional[str] = Field(None, description="Feedback source filter")
    customer_id: Optional[str] = Field(None, description="Customer ID filter")
    language: Optional[str] = Field(None, description="Detected language filter")

class ChatQueryRequest(BaseModel):
    question: str = Field(..., description="The question to ask about feedback data")
    filters: Optional[QueryFilters] = Field(None, description="Optional filters to apply to the query")

class Citation(BaseModel):
    feedback_id: str = Field(..., description="UUID of the feedback item")
    topic_id: Optional[int] = Field(None, description="Topic ID if applicable")

class ChatQueryResponse(BaseModel):
    answer: str = Field(..., description="The agent's answer to the question")
    citations: List[Citation] = Field(default_factory=list, description="List of citations used in the answer")

class QueryRequest(BaseModel):  # Keep for backward compatibility
    query: str
    context_limit: int = 10

class QueryResponse(BaseModel):  # Keep for backward compatibility
    query: str
    answer: str
    sources: list = []
    confidence: float = 0.0
    tool_usage: list = []
    success: bool = True
    timestamp: Optional[str] = None

class ConversationHistoryResponse(BaseModel):
    conversations: list = []
    total: int = 0
    has_more: bool = False

# Token and timeout limits
MAX_TOKENS = 4000  # Maximum tokens for OpenAI requests
REQUEST_TIMEOUT = 30  # Maximum time for request processing in seconds
MAX_QUESTION_LENGTH = 1000  # Maximum question length in characters

def estimate_token_count(text: str) -> int:
    """Rough estimate of token count for text (approx 4 chars per token)."""
    return len(text) // 4

def validate_token_limits(question: str, filters: Optional[QueryFilters] = None) -> None:
    """Validate that the request stays within token limits."""
    # Estimate tokens for the question
    question_tokens = estimate_token_count(question)

    if question_tokens > MAX_TOKENS * 0.8:  # Leave room for response
        raise HTTPException(
            status_code=413,
            detail=f"Question too long. Estimated {question_tokens} tokens exceeds limit of {int(MAX_TOKENS * 0.8)}"
        )

    # Check question length
    if len(question) > MAX_QUESTION_LENGTH:
        raise HTTPException(
            status_code=413,
            detail=f"Question too long. {len(question)} characters exceeds limit of {MAX_QUESTION_LENGTH}"
        )

    # Estimate tokens for filters description
    filter_text = ""
    if filters:
        filter_parts = []
        if filters.date_range:
            if filters.date_range.start_date:
                filter_parts.append(f"from {filters.date_range.start_date}")
            if filters.date_range.end_date:
                filter_parts.append(f"until {filters.date_range.end_date}")
        if filters.sentiment is not None:
            filter_parts.append("sentiment filter")
        if filters.topic_ids:
            filter_parts.append(f"{len(filters.topic_ids)} topic filters")
        if filters.source:
            filter_parts.append(f"source {filters.source}")
        if filters.customer_id:
            filter_parts.append(f"customer {filters.customer_id}")
        if filters.language:
            filter_parts.append(f"language {filters.language}")
        filter_text = " ".join(filter_parts)

    filter_tokens = estimate_token_count(filter_text)
    total_estimated_tokens = question_tokens + filter_tokens

    if total_estimated_tokens > MAX_TOKENS:
        raise HTTPException(
            status_code=413,
            detail=f"Request too large. Estimated {total_estimated_tokens} tokens exceeds limit of {MAX_TOKENS}"
        )

def extract_citations_from_response(response_text: str, db: Session) -> List[Citation]:
    """Extract feedback_id citations from response text and get associated topic_ids."""
    import re
    from ..repositories import FeedbackRepository

    citations = []
    feedback_repo = FeedbackRepository(db)

    # Find all feedback_id patterns in the response
    feedback_id_pattern = r'feedback_id[:\s]+([a-f0-9\-]{36})'
    feedback_ids = re.findall(feedback_id_pattern, response_text, re.IGNORECASE)

    for feedback_id_str in feedback_ids:
        try:
            # Convert to UUID and get feedback with annotations
            from uuid import UUID
            feedback_uuid = UUID(feedback_id_str)

            feedback = feedback_repo.get_feedback_with_annotations(feedback_uuid)
            if feedback and feedback.get('nlp_annotations'):
                # Get topic_id from the first annotation (assuming one primary annotation per feedback)
                topic_id = feedback['nlp_annotations'][0].get('topic_id')
                citations.append(Citation(
                    feedback_id=feedback_id_str,
                    topic_id=topic_id
                ))
            else:
                # Citation without topic_id if no annotations
                citations.append(Citation(
                    feedback_id=feedback_id_str,
                    topic_id=None
                ))

        except (ValueError, Exception):
            logger.warning(f"Could not process citation for feedback_id {feedback_id_str}")
            # Add citation even if we can't get topic_id
            citations.append(Citation(
                feedback_id=feedback_id_str,
                topic_id=None
            ))

    return citations

def apply_filters_to_query(query: str, filters: Optional[QueryFilters]) -> str:
    """Apply filters to the query by modifying the system prompt."""
    if not filters:
        return query

    filter_descriptions = []

    if filters.date_range:
        if filters.date_range.start_date:
            filter_descriptions.append(f"from {filters.date_range.start_date}")
        if filters.date_range.end_date:
            filter_descriptions.append(f"until {filters.date_range.end_date}")

    if filters.sentiment is not None:
        sentiment_map = {-1: "negative", 0: "neutral", 1: "positive"}
        filter_descriptions.append(f"with {sentiment_map[filters.sentiment]} sentiment")

    if filters.topic_ids:
        filter_descriptions.append(f"related to topics {filters.topic_ids}")

    if filters.source:
        filter_descriptions.append(f"from source '{filters.source}'")

    if filters.customer_id:
        filter_descriptions.append(f"from customer '{filters.customer_id}'")

    if filters.language:
        filter_descriptions.append(f"in language '{filters.language}'")

    if filter_descriptions:
        filter_text = " and ".join(filter_descriptions)
        return f"{query} (filtered to show only feedback {filter_text})"

    return query

@router.post("/chat/query", response_model=ChatQueryResponse)
async def chat_query(
    request: ChatQueryRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """Process a natural language query about customer feedback with filters and citations."""
    start_time = time.time()

    try:
        # Validate token limits first
        validate_token_limits(request.question, request.filters)

        # Get the feedback analysis agent
        agent = await get_feedback_agent()

        # Apply filters to the query
        filtered_query = apply_filters_to_query(request.question, request.filters)

        # Log the incoming request
        logger.info(f"Processing query: '{request.question[:100]}{'...' if len(request.question) > 100 else ''}' "
                   f"with filters: {request.filters.dict() if request.filters else 'none'}")

        # Create a timeout task with proper error handling
        async def process_with_timeout():
            try:
                # Process the query using the agent (runs in thread pool to not block event loop)
                result = await asyncio.get_event_loop().run_in_executor(
                    None, agent.analyze_feedback, filtered_query
                )
                return result
            except Exception as e:
                logger.error(f"Agent processing error: {e}")
                raise

        # Execute with timeout
        try:
            result = await asyncio.wait_for(process_with_timeout(), timeout=REQUEST_TIMEOUT)
        except asyncio.TimeoutError:
            logger.warning(f"Query timed out after {REQUEST_TIMEOUT} seconds: {request.question[:100]}")
            raise HTTPException(
                status_code=408,
                detail=f"Request timed out after {REQUEST_TIMEOUT} seconds"
            )

        # Validate response grounding
        validation = agent.validate_response_grounding(result["answer"])

        if not validation["is_grounded"]:
            logger.warning(f"Response may not be properly grounded: {validation['issues']}")

        # Extract citations from the response
        citations = extract_citations_from_response(result["answer"], db)

        processing_time = time.time() - start_time
        logger.info(f"Query processed in {processing_time:.2f}s with {len(citations)} citations")

        # Add performance headers
        req.state.process_time = processing_time

        return ChatQueryResponse(
            answer=result["answer"],
            citations=citations
        )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Failed to process query after {processing_time:.2f}s: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

@router.post("/query", response_model=QueryResponse)
async def ask_question(request: QueryRequest, db: Session = Depends(get_db)):
    """Process a natural language query about customer feedback using LangChain agent"""
    try:
        # Get the feedback analysis agent
        agent = get_feedback_agent()

        # Process the query using the agent
        result = agent.analyze_feedback(request.query)

        # Validate response grounding
        validation = agent.validate_response_grounding(result["answer"])

        if not validation["is_grounded"]:
            logger.warning(f"Response may not be properly grounded: {validation['issues']}")

        # Return the response with agent results
        return QueryResponse(
            query=result["query"],
            answer=result["answer"],
            sources=[],  # Could be populated with cited feedback_ids
            confidence=0.9 if result["success"] else 0.0,  # High confidence for successful analyses
            tool_usage=result.get("tool_usage", []),
            success=result["success"],
            timestamp=result.get("timestamp")
        )

    except Exception as e:
        logger.error(f"Failed to process query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

@router.get("/conversations", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get conversation history from the LangChain agent"""
    try:
        agent = get_feedback_agent()
        history = agent.get_conversation_history()

        # Apply pagination
        total = len(history)
        start_idx = max(0, total - offset - limit)
        end_idx = max(0, total - offset)

        paginated_history = history[start_idx:end_idx]

        return ConversationHistoryResponse(
            conversations=paginated_history,
            total=total,
            has_more=(offset + limit) < total
        )

    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        return ConversationHistoryResponse(
            conversations=[],
            total=0,
            has_more=False
        )

@router.post("/feedback/{feedback_id}/clarify")
async def clarify_feedback(
    feedback_id: str,
    clarification_query: str,
    db: Session = Depends(get_db)
):
    """Get clarification about specific feedback (placeholder)"""
    try:
        # Validate feedback exists
        from ..repositories import FeedbackRepository
        repo = FeedbackRepository(db)

        try:
            from uuid import UUID
            feedback_uuid = UUID(feedback_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid feedback ID format")

        feedback = repo.get_feedback_with_annotations(feedback_uuid)
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback item not found")

        # Return clarification response
        return {
            "feedback_id": feedback_id,
            "original_text": feedback.get("text", ""),
            "clarification_query": clarification_query,
            "clarification": "This is a placeholder clarification response. The full clarification system is not yet implemented.",
            "confidence": 0.0
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process clarification: {str(e)}")

@router.post("/clear-memory")
async def clear_agent_memory():
    """Clear the LangChain agent's conversation memory"""
    try:
        agent = get_feedback_agent()
        agent.clear_memory()
        return {"message": "Conversation memory cleared successfully"}

    except Exception as e:
        logger.error(f"Failed to clear agent memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear memory: {str(e)}")

@router.get("/suggestions")
async def get_query_suggestions(db: Session = Depends(get_db)):
    """Get suggested queries based on available data"""
    try:
        # Get some basic stats to generate suggestions
        from ..repositories import AnalyticsRepository
        repo = AnalyticsRepository(db)

        total_feedback = repo.execute_query(
            "SELECT COUNT(*) FROM feedback",
            fetch="scalar"
        )

        top_sources = repo.get_source_stats()
        top_topics = repo.get_topic_distribution(min_feedback_count=5, limit=10)

        suggestions = [
            "What are the main topics in customer feedback?",
            "How has sentiment changed over time?",
            "What are the most common customer complaints?",
            "Which sources provide the most feedback?",
            "Show me examples of positive feedback",
            "What topics have the most negative sentiment?",
            "Generate a weekly summary report",
            "Show me feedback trends over the last month"
        ]

        if total_feedback and total_feedback > 100:
            suggestions.insert(0, "Show me recent feedback trends")

        return {
            "suggestions": suggestions,
            "context": {
                "total_feedback": total_feedback,
                "top_sources": [s.get("source") for s in top_sources[:3]] if top_sources else [],
                "top_topics": [t.get("label") for t in top_topics[:3]] if top_topics else []
            }
        }

    except Exception as e:
        # Return basic suggestions if analytics fail
        return {
            "suggestions": [
                "What are the main topics in customer feedback?",
                "How has sentiment changed over time?",
                "What are the most common customer complaints?",
                "Show me examples of positive feedback",
                "Generate a weekly summary report"
            ],
            "context": {}
        }
