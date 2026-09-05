"""Benchmark types and evaluation models for Recon-AI Phase 3."""

from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvaluationOutcome(str, Enum):
    """Whether the engine's decision on a ground-truth case was correct."""
    CORRECT_RESOLUTION = "CORRECT_RESOLUTION"
    CORRECT_REVIEW = "CORRECT_REVIEW"
    CORRECT_UNRESOLVED = "CORRECT_UNRESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"
    INCORRECT_MATCH = "INCORRECT_MATCH"


class FailureReason(str, Enum):
    """Evidence-based classification of why the engine failed on a case."""
    REFERENCE_NOT_FOUND = "REFERENCE_NOT_FOUND"
    DATE_WINDOW_TOO_STRICT = "DATE_WINDOW_TOO_STRICT"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    BATCH_SEARCH_LIMIT = "BATCH_SEARCH_LIMIT"
    MISSING_IDENTIFIER = "MISSING_IDENTIFIER"
    AMBIGUOUS_CANDIDATES = "AMBIGUOUS_CANDIDATES"
    UNSUPPORTED_PATTERN = "UNSUPPORTED_PATTERN"
    WRONG_BANK_MATCHED = "WRONG_BANK_MATCHED"
    WRONG_GATEWAY_SET = "WRONG_GATEWAY_SET"
    OTHER = "OTHER"


class CaseEvaluation(BaseModel):
    """Evaluation result for a single ground-truth case."""
    case_id: str
    scenario: str
    outcome: EvaluationOutcome

    # Ground truth
    gt_erp_order_ids: List[str] = Field(default_factory=list)
    gt_gateway_transaction_ids: List[str] = Field(default_factory=list)
    gt_settlement_id: Optional[str] = None
    gt_bank_transaction_ids: List[str] = Field(default_factory=list)
    gt_expected_relationship: str = ""
    gt_expected_net_amount: float = 0.0
    gt_actual_bank_amount: Optional[float] = None
    gt_root_cause: Optional[str] = None
    gt_is_exception: bool = False

    # Engine prediction (if matched)
    engine_reconciliation_id: Optional[str] = None
    engine_status: Optional[str] = None
    engine_match_type: Optional[str] = None
    engine_root_cause: Optional[str] = None
    engine_gateway_ids: List[str] = Field(default_factory=list)
    engine_bank_ids: List[str] = Field(default_factory=list)
    engine_expected_amount: Optional[float] = None
    engine_actual_amount: Optional[float] = None
    engine_confidence: Optional[float] = None
    engine_explanation: Optional[str] = None

    # Financial impact
    financial_value: float = 0.0
    financial_impact: float = 0.0  # signed difference

    # Failure analysis
    failure_reason: Optional[FailureReason] = None
    failure_detail: Optional[str] = None


class ScenarioMetrics(BaseModel):
    """Per-scenario performance breakdown."""
    scenario: str
    total_cases: int = 0
    correct: int = 0
    incorrect: int = 0
    resolved: int = 0
    review: int = 0
    unresolved: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    match_rate: float = 0.0
    value_reconciled: float = 0.0
    value_total: float = 0.0
    value_reconciliation_percentage: float = 0.0


class MatchTypeMetrics(BaseModel):
    """Per-match-type performance breakdown."""
    match_type: str
    count: int = 0
    correct: int = 0
    incorrect: int = 0
    financial_value: float = 0.0
    accuracy: float = 0.0


class BenchmarkReport(BaseModel):
    """Top-level benchmark report structure."""
    # Metadata
    benchmark_metadata: Dict[str, Any] = Field(default_factory=dict)

    # Dataset counts
    dataset: Dict[str, int] = Field(default_factory=dict)

    # Decision quality
    decisions: Dict[str, int] = Field(default_factory=dict)

    # Accuracy metrics
    accuracy: Dict[str, Any] = Field(default_factory=dict)

    # Financial metrics
    financial: Dict[str, Any] = Field(default_factory=dict)

    # Performance metrics
    performance: Dict[str, Any] = Field(default_factory=dict)

    # Scenario breakdown
    scenarios: Dict[str, Any] = Field(default_factory=dict)

    # Match type breakdown
    match_types: Dict[str, Any] = Field(default_factory=dict)

    # Review quality
    review_quality: Dict[str, Any] = Field(default_factory=dict)

    # Autonomous resolution quality
    autonomous_resolution: Dict[str, Any] = Field(default_factory=dict)

    # Failures list
    failures: List[Dict[str, Any]] = Field(default_factory=list)

    # False positive details
    false_positive_details: List[Dict[str, Any]] = Field(default_factory=list)

    # False negative details
    false_negative_details: List[Dict[str, Any]] = Field(default_factory=list)

    # Case evaluations (all)
    case_evaluations: List[Dict[str, Any]] = Field(default_factory=list)
