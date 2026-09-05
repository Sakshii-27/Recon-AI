from pydantic import BaseModel, Field

class HistoricalAnalysisResult(BaseModel):
    similar_cases_found: int = Field(default=0)
    comparison_summary: str = Field(..., description="Summary of how this case compares to historical examples")

HISTORICAL_ANALYST_PROMPT = """
You are the Historical Analyst.

### TASK
Compare the current exception against the retrieved historical cases.
Identify matching characteristics and important differences.
Determine if history strengthens or weakens the current hypothesis.
Do not blindly copy past decisions.

### RETRIEVED HISTORICAL CASES
{historical_cases}

### EVIDENCE
{structured_evidence}
"""
