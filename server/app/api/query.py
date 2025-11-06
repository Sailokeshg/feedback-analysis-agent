from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..services.query_service import QueryService

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: list

@router.post("/query", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """Process a natural language query about customer feedback"""
    try:
        query_service = QueryService()
        result = await query_service.process_query(request.query)

        return QueryResponse(
            query=request.query,
            answer=result["answer"],
            sources=result["sources"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")
