"""Type definitions and models for Recon-AI reconciliation engine."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReconciliationStatus(str, Enum):
    RESOLVED = "RESOLVED"
    REVIEW = "REVIEW"
    UNRESOLVED = "UNRESOLVED"


class MatchType(str, Enum):
    EXACT_1_TO_1 = "EXACT_1_TO_1"
    FEE_RECONCILED = "FEE_RECONCILED"
    BATCH_N_TO_1 = "BATCH_N_TO_1"
    PARTIAL = "PARTIAL"
    MISSING_BANK = "MISSING_BANK"
    MISSING_ERP = "MISSING_ERP"
    DUPLICATE = "DUPLICATE"
    REFERENCE_MATCH = "REFERENCE_MATCH"
    DATE_AMOUNT_MATCH = "DATE_AMOUNT_MATCH"
    UNRESOLVED = "UNRESOLVED"


class RootCause(str, Enum):
    EXACT_MATCH = "EXACT_MATCH"
    FEE_MISMATCH = "FEE_MISMATCH"
    MDR_GST = "MDR_GST"
    BATCH_SETTLEMENT = "BATCH_SETTLEMENT"
    T_PLUS_1 = "T_PLUS_1"
    T_PLUS_2 = "T_PLUS_2"
    REFUND = "REFUND"
    CHARGEBACK = "CHARGEBACK"
    PARTIAL_SETTLEMENT = "PARTIAL_SETTLEMENT"
    DUPLICATE = "DUPLICATE"
    MISSING_BANK = "MISSING_BANK"
    MISSING_ERP = "MISSING_ERP"
    REFERENCE_MISMATCH = "REFERENCE_MISMATCH"
    FEE_ANOMALY = "FEE_ANOMALY"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"  # For genuinely ambiguous cases


class FinancialEvidence(BaseModel):
    captured_amount: str
    expected_mdr: str
    expected_gst: str
    expected_net: str
    actual_bank_amount: str
    difference: str
    refund_amount: Optional[str] = "0.00"
    chargeback_amount: Optional[str] = "0.00"


class ReconciliationEvidence(BaseModel):
    matched_by: List[str] = Field(default_factory=list)
    erp_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    gateway_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    bank_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    financial_evidence: Optional[FinancialEvidence] = None


class ReconciliationResult(BaseModel):
    reconciliation_id: str
    status: ReconciliationStatus
    match_type: MatchType
    root_cause: RootCause

    erp_order_ids: List[str] = Field(default_factory=list)
    gateway_transaction_ids: List[str] = Field(default_factory=list)
    settlement_id: Optional[str] = None
    bank_transaction_ids: List[str] = Field(default_factory=list)

    expected_amount: float
    actual_amount: float
    difference: float

    confidence: float
    evidence: ReconciliationEvidence
    explanation: str
    recommended_action: Optional[str] = None
