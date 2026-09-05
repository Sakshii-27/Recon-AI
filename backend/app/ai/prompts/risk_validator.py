from pydantic import BaseModel, Field
from typing import List

class RiskValidationResult(BaseModel):
    approved: bool = Field(..., description="Whether the proposed decision is safe and well-supported")
    risk_concerns: List[str] = Field(default_factory=list, description="List of concerns or contradictions found")
    final_decision: str = Field(..., description="The final decision. May downgrade to INSUFFICIENT_EVIDENCE or HUMAN_REVIEW")
    recommended_action: str = Field(..., description="What the human operator should do")

RISK_VALIDATOR_PROMPT = """
You are the Risk and Contradiction Validator.

### TASK
You must challenge the proposed decision.
Look specifically for:
- false duplicate signals (e.g. failed retries mistaken for captures)
- unsupported assumptions
- missing settlement evidence
- policy conflicts

You have the authority to REJECT the proposed decision. If the evidence is weak, you MUST reject it.
If rejected, change the final_decision to INSUFFICIENT_EVIDENCE or HUMAN_REVIEW.

### EVIDENCE
{structured_evidence}

### PROPOSED DECISION
Decision: {decision}
Confidence: {confidence}
Reasoning: {reasoning}
"""
