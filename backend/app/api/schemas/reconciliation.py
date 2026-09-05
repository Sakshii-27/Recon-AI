"""Reconciliation API Schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.app.domain.finance_rules import DEFAULT_SEED


class ReconciliationRunRequest(BaseModel):
    """Request to run a deterministic reconciliation batch."""
    records: int = Field(default=100, description="Number of synthetic cases to generate", ge=13, le=10000)
    seed: int = Field(default=DEFAULT_SEED, description="Random seed for synthetic generation")


class ReconciliationSummary(BaseModel):
    """High-level summary of the reconciliation run."""
    total_records: int
    matched: int
    exceptions: int
    match_rate: float
    value_reconciled: float
    safe_autonomous_rate: float


class ReconciliationResponse(BaseModel):
    """Full response from a reconciliation run."""
    summary: ReconciliationSummary
    matches: List[Dict[str, Any]] = Field(default_factory=list, description="Correctly matched records")
    exceptions: List[Dict[str, Any]] = Field(default_factory=list, description="Unresolved or review exceptions")
    decisions: List[Dict[str, Any]] = Field(default_factory=list, description="All engine decisions")
    financial_summary: Dict[str, Any] = Field(default_factory=dict, description="Financial coverage summary")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Run metadata (seed, timing, etc.)")
