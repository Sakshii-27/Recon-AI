"""Evidence and deterministic explanation builder."""

from typing import List, Dict, Any, Optional

from backend.app.reconciliation.types import (
    FinancialEvidence,
    ReconciliationEvidence,
)
from backend.app.domain.models import ERPOrder, GatewayTransaction, BankTransaction


def build_erp_evidence(orders: List[ERPOrder]) -> List[Dict[str, Any]]:
    return [
        {
            "order_id": o.order_id,
            "order_reference": o.order_reference,
            "gross_amount": o.gross_amount,
            "order_date": o.order_date,
        }
        for o in orders
    ]


def build_gateway_evidence(txns: List[GatewayTransaction]) -> List[Dict[str, Any]]:
    return [
        {
            "gateway_transaction_id": t.gateway_transaction_id,
            "order_reference": t.order_reference,
            "captured_amount": t.captured_amount,
            "gateway_fee": t.gateway_fee,
            "gst_on_fee": t.gst_on_fee,
            "refund_amount": t.refund_amount,
            "chargeback_amount": t.chargeback_amount,
            "settlement_id": t.settlement_id,
        }
        for t in txns
    ]


def build_bank_evidence(txns: List[BankTransaction]) -> List[Dict[str, Any]]:
    return [
        {
            "bank_transaction_id": b.bank_transaction_id,
            "description": b.description,
            "reference": b.reference,
            "credit_amount": b.credit_amount,
            "bank_utr": b.bank_utr,
            "transaction_date": b.transaction_date,
        }
        for b in txns
    ]


def build_financial_evidence(
    captured_amount: float,
    expected_mdr: float,
    expected_gst: float,
    expected_net: float,
    actual_bank_amount: float,
    difference: float,
    refund_amount: float = 0.0,
    chargeback_amount: float = 0.0,
) -> FinancialEvidence:
    return FinancialEvidence(
        captured_amount=f"{captured_amount:.2f}",
        expected_mdr=f"{expected_mdr:.2f}",
        expected_gst=f"{expected_gst:.2f}",
        expected_net=f"{expected_net:.2f}",
        actual_bank_amount=f"{actual_bank_amount:.2f}",
        difference=f"{difference:.2f}",
        refund_amount=f"{refund_amount:.2f}",
        chargeback_amount=f"{chargeback_amount:.2f}",
    )


def generate_explanation(
    match_type: str,
    evidence: ReconciliationEvidence,
    expected_net: float,
    actual_bank_amount: float,
    difference: float,
) -> str:
    """Deterministically generates a human-readable explanation from the structured evidence."""
    lines = []
    
    if match_type == "EXACT_1_TO_1":
        lines.append("Matched 1:1 using exact deterministic identifiers.")
    elif match_type == "FEE_RECONCILED":
        lines.append("Matched 1:1 with fee deduction verified.")
    elif match_type == "BATCH_N_TO_1":
        lines.append(f"Matched batch settlement: {len(evidence.gateway_evidence)} transactions to 1 bank deposit.")
    elif match_type == "MISSING_BANK":
        lines.append("Gateway settlement exists, but bank credit is missing.")
    elif match_type == "MISSING_ERP":
        lines.append("Gateway transaction exists, but ERP order is missing.")
    elif match_type == "DUPLICATE":
        lines.append("Suspected duplicate gateway capture or bank deposit.")
    elif match_type == "PARTIAL":
        lines.append("Partial settlement payout received in bank.")
    elif match_type == "UNRESOLVED":
        lines.append("Unresolved discrepancy or insufficient evidence.")
    else:
        lines.append(f"Matched via {match_type}.")

    lines.append(f"Expected net settlement: ₹{expected_net:,.2f}")
    if match_type != "MISSING_BANK":
        lines.append(f"Bank credit: ₹{actual_bank_amount:,.2f}")
    lines.append(f"Difference: ₹{difference:,.2f}")

    if evidence.financial_evidence:
        fe = evidence.financial_evidence
        lines.append(
            f"Gross captured: ₹{float(fe.captured_amount):,.2f}. "
            f"MDR deducted: ₹{float(fe.expected_mdr):,.2f}. "
            f"GST deducted: ₹{float(fe.expected_gst):,.2f}."
        )
        if float(fe.refund_amount) > 0:
            lines.append(f"Refund deducted: ₹{float(fe.refund_amount):,.2f}.")
        if float(fe.chargeback_amount) > 0:
            lines.append(f"Chargeback deducted: ₹{float(fe.chargeback_amount):,.2f}.")

    return "\n".join(lines)
