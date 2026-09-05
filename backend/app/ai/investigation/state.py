from typing import Dict, Any, TypedDict, Optional
from backend.app.ai.schemas import (
    EvidenceAnalysisResult,
    PolicyAnalysisResult,
    HistoricalAnalysisResult,
    RiskValidationResult
)

class InvestigationState(TypedDict):
    # Inputs
    structured_evidence: Dict[str, Any]
    policies: list[str]
    historical_cases: list[str]
    
    # Processed components
    evidence_analysis: Optional[EvidenceAnalysisResult]
    policy_analysis: Optional[PolicyAnalysisResult]
    historical_analysis: Optional[HistoricalAnalysisResult]
    
    # Intermediate decision
    proposed_decision: Optional[str]
    proposed_confidence: Optional[float]
    proposed_reasoning: Optional[str]
    supporting_evidence: list[str]
    policy_basis: list[str]
    similar_cases: list[str]
    
    # Final output
    risk_validation: Optional[RiskValidationResult]
    
    # Tracking
    source_types: Dict[str, str]
    errors: list[str]
