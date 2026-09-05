from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class AIResolutionRequest(BaseModel):
    exception_id: str = Field(..., description="The ID of the exception to investigate")

class AIResolutionResponse(BaseModel):
    exception_id: str
    decision: str = Field(..., description="Must be one of: LIKELY_MATCH, LIKELY_DUPLICATE, LIKELY_BATCH_SETTLEMENT, LIKELY_MISSING_ERP, UNRESOLVED")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the decision, from 0.0 to 1.0")
    reasoning: str = Field(..., description="Detailed explanation of the analysis")
    supporting_evidence: List[str] = Field(default_factory=list, description="Specific evidence elements that supported this conclusion")
    recommended_action: str = Field(..., description="What the operator should do")
    human_review_required: bool = Field(default=True, description="Whether human review is needed")


# --- Stage Result Models ---

class EvidenceAnalysisResult(BaseModel):
    summary: str = Field(..., description="Summary of evidence")
    flags: List[str] = Field(default_factory=list, description="Anomalies or patterns detected")

class PolicyAnalysisResult(BaseModel):
    applicable_policies: List[str] = Field(default_factory=list)
    implications: str = Field(..., description="How policies apply here")

class HistoricalAnalysisResult(BaseModel):
    similar_cases_found: int = Field(default=0)
    comparison_summary: str = Field(..., description="Comparison with past cases")

class RiskValidationResult(BaseModel):
    approved: bool = Field(..., description="Whether the decision was approved")
    risk_concerns: List[str] = Field(default_factory=list, description="Concerns flagged by validator")
    final_decision: str = Field(default="INSUFFICIENT_EVIDENCE", description="The final decision. May downgrade to INSUFFICIENT_EVIDENCE or HUMAN_REVIEW")
    recommended_action: str = Field(default="Manual Review Required", description="What the human operator should do")


class AIInvestigationResponse(BaseModel):
    """Full evidence-grounded AI investigation result."""
    exception_id: str
    decision: str = Field(..., description="Final decision from Risk Validator")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Final consolidated reasoning")
    
    # Stage results
    evidence_analysis: EvidenceAnalysisResult
    policy_analysis: PolicyAnalysisResult
    historical_analysis: HistoricalAnalysisResult
    risk_validation: RiskValidationResult
    
    # Structured output fields
    supporting_evidence: List[str] = Field(default_factory=list)
    policy_basis: List[str] = Field(default_factory=list)
    similar_cases: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    recommended_action: str = Field(...)
    human_review_required: bool = Field(default=True)
    
    # Source attribution
    source_types: Dict[str, str] = Field(default_factory=dict, description="e.g. {'policy_1': 'policy_rag'}")
    
    # Flags for graceful fallback observability
    is_fallback: bool = Field(default=False, description="True if AI failed and fallback was used")
