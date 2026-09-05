from pydantic import BaseModel, Field
from typing import List

class PolicyAnalysisResult(BaseModel):
    applicable_policies: List[str] = Field(default_factory=list, description="Titles of policies that apply to this case")
    implications: str = Field(..., description="How the policies affect the interpretation of this evidence")

POLICY_ANALYST_PROMPT = """
You are the Policy Analyst.

### TASK
Given the retrieved finance policies and the structured evidence, identify which rules apply.
Do not invent policies. Use only what is retrieved.

### RETRIEVED POLICIES
{policies}

### EVIDENCE
{structured_evidence}
"""
