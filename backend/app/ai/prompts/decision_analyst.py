from pydantic import BaseModel, Field
from typing import List

class DecisionProposal(BaseModel):
    decision: str = Field(..., description="Must be one of: LIKELY_DUPLICATE, VALID_BATCH_SETTLEMENT, LIKELY_MISSING_ERP, INSUFFICIENT_EVIDENCE")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Explain how the evidence, policies, and history led to this decision")
    supporting_evidence: List[str] = Field(default_factory=list)
    policy_basis: List[str] = Field(default_factory=list)
    similar_cases: List[str] = Field(default_factory=list)

DECISION_ANALYST_PROMPT = """
You are the Decision Analyst.

### TASK
Using ONLY the structured evidence, the evidence analysis, applicable policies, and historical cases, propose a classification.
Do not invent new accounting states. Do not guess if evidence is insufficient.
If you are unsure, choose INSUFFICIENT_EVIDENCE.

### EVIDENCE ANALYSIS
{evidence_analysis}

### POLICY ANALYSIS
{policy_analysis}

### HISTORICAL ANALYSIS
{historical_analysis}
"""
