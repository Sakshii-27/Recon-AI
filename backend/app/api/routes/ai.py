"""AI Route."""
from fastapi import APIRouter, HTTPException

from backend.app.services.reconciliation_service import reconciliation_service
from backend.app.ai.resolver import investigate_exception, investigate_exception_v2
from backend.app.ai.schemas import AIResolutionRequest, AIResolutionResponse, AIInvestigationResponse

router = APIRouter()

@router.post("/resolve", response_model=AIResolutionResponse)
def resolve_with_ai(request: AIResolutionRequest):
    """Investigates an exception using AI and returns a recommendation."""
    # 1. Retrieve the existing exception
    exception = reconciliation_service.get_exception(request.exception_id)
    if not exception:
        raise HTTPException(status_code=404, detail=f"Exception {request.exception_id} not found in latest run")
    
    # 2. Invoke the AI resolver with the bounded payload
    # We use model_dump() to get the dict representation matching what the resolver expects
    exception_dict = exception.model_dump()
    try:
        recommendation = investigate_exception(exception_dict)
        return recommendation
    except Exception as e:
        # Graceful failure handling
        return AIResolutionResponse(
            exception_id=request.exception_id,
            decision="UNRESOLVED",
            confidence=0.0,
            reasoning=f"AI Investigation failed: {str(e)}",
            supporting_evidence=[],
            recommended_action="Manual investigation required.",
            human_review_required=True
        )

@router.post("/investigate", response_model=AIInvestigationResponse)
def investigate_with_ai_v2(request: AIResolutionRequest):
    """Investigates an exception using the V2 LangGraph + RAG pipeline."""
    # 1. Retrieve the existing exception
    exception = reconciliation_service.get_exception(request.exception_id)
    if not exception:
        raise HTTPException(status_code=404, detail=f"Exception {request.exception_id} not found in latest run")
    
    # 2. Invoke the AI resolver with the bounded payload
    exception_dict = exception.model_dump()
    try:
        recommendation = investigate_exception_v2(exception_dict)
        return recommendation
    except Exception as e:
        # Graceful failure handling
        from backend.app.ai.schemas import EvidenceAnalysisResult, PolicyAnalysisResult, HistoricalAnalysisResult, RiskValidationResult
        return AIInvestigationResponse(
            exception_id=request.exception_id,
            decision="UNRESOLVED",
            confidence=0.0,
            reasoning=f"AI Investigation Pipeline failed: {str(e)}",
            evidence_analysis=EvidenceAnalysisResult(summary="N/A", flags=[]),
            policy_analysis=PolicyAnalysisResult(applicable_policies=[], implications="N/A"),
            historical_analysis=HistoricalAnalysisResult(similar_cases_found=0, comparison_summary="N/A"),
            risk_validation=RiskValidationResult(approved=False, risk_concerns=[str(e)], final_decision="UNRESOLVED", recommended_action="Manual investigation required."),
            supporting_evidence=[],
            policy_basis=[],
            similar_cases=[],
            risk_flags=["Pipeline Failure"],
            recommended_action="Manual investigation required.",
            human_review_required=True,
            source_types={},
            is_fallback=True
        )
