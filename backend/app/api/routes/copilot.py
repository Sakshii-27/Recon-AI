"""Copilot Route."""
from fastapi import APIRouter, HTTPException
from backend.app.copilot.schemas import CopilotQueryRequest, CopilotQueryResponse
from backend.app.copilot.service import copilot_service

router = APIRouter()

@router.post("/query", response_model=CopilotQueryResponse)
def query_copilot(request: CopilotQueryRequest):
    """Answers natural language questions using deterministic backend data."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
        
    try:
        return copilot_service.query(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
