"""Schemas for the Finance Copilot."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CopilotQueryRequest(BaseModel):
    question: str = Field(..., description="The user's natural language question.")
    exception_id: Optional[str] = Field(None, description="Optional specific exception ID context if the user is asking from the workbench.")

class CopilotQueryResponse(BaseModel):
    answer: str = Field(..., description="The natural language answer to the user's question.")
    supporting_data: Dict[str, Any] = Field(default_factory=dict, description="Deterministic financial values or counts supporting the answer.")
    source_sections: List[str] = Field(default_factory=list, description="Which subsystem(s) provided the authoritative data (e.g., 'Cash Position').")
    confidence: str = Field(..., description="Confidence in the response (e.g., 'HIGH', 'N/A').")
    requires_human_review: bool = Field(default=False, description="True if the response involves AI interpretation or recommendation.")
