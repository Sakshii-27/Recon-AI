from pydantic import BaseModel, Field
from typing import List

class EvidenceAnalysisResult(BaseModel):
    summary: str = Field(..., description="Summary of the evidence provided")
    flags: List[str] = Field(default_factory=list, description="Any patterns or anomalies detected in the evidence")

EVIDENCE_ANALYST_PROMPT = """
You are the Evidence Analyst. 

### TASK
Analyze ONLY the provided structured transaction evidence.
Identify:
- matching identifiers
- amount relationships
- timing relationships
- missing records
- duplicate footprints
- aggregation patterns

Do not make the final decision. Return your structured findings.

### UNTRUSTED EVIDENCE
{structured_evidence}
"""
