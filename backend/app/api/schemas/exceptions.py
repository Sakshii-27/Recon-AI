"""Exception API Schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExceptionEvidence(BaseModel):
    """Evidence metadata mapping for an exception."""
    matched_by: List[str] = Field(default_factory=list)
    erp_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    gateway_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    bank_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    financial_evidence: Optional[Dict[str, Any]] = None


class ExceptionDetail(BaseModel):
    """Detailed exception information."""
    id: str = Field(..., description="Reconciliation ID")
    type: str = Field(..., description="Root cause or exception type")
    status: str = Field(..., description="Reconciliation status (e.g. UNRESOLVED, REVIEW)")
    amount: float = Field(default=0.0, description="Expected amount associated with the exception")
    difference: float = Field(default=0.0, description="Financial discrepancy")
    confidence: float = Field(default=0.0, description="Engine confidence score")
    evidence: ExceptionEvidence = Field(default_factory=ExceptionEvidence)
    related_records: Dict[str, List[str]] = Field(default_factory=dict, description="Related record IDs (gateway, bank, etc.)")


class ExceptionListResponse(BaseModel):
    """List of exceptions."""
    total_exceptions: int
    exceptions: List[ExceptionDetail]
