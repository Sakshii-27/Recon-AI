"""Tier 2: Financial Reconciliation & Validation."""

from decimal import Decimal
from typing import List, Optional, Tuple

from backend.app.domain.finance_rules import (
    calculate_expected_net_settlement,
    calculate_total_fee,
    round_currency,
)
from backend.app.domain.models import BankTransaction, ERPOrder, GatewaySettlement, GatewayTransaction
from backend.app.reconciliation.config import AMOUNT_TOLERANCE, AUTO_RESOLVE_THRESHOLD, GST_RATE, MDR_RATE
from backend.app.reconciliation.evidence import (
    build_bank_evidence,
    build_erp_evidence,
    build_financial_evidence,
    build_gateway_evidence,
    generate_explanation,
)
from backend.app.reconciliation.types import (
    MatchType,
    ReconciliationEvidence,
    ReconciliationResult,
    ReconciliationStatus,
    RootCause,
)


class Tier2FinancialValidator:
    """Validates 1:1 financial relationships and detects anomalies."""

    def __init__(self):
        pass

    def evaluate_1_to_1_match(
        self,
        erp: Optional[ERPOrder],
        gtw: GatewayTransaction,
        stl: Optional[GatewaySettlement],
        bnk: BankTransaction,
        base_confidence: float,
        matched_by: List[str],
        reconciliation_id: str
    ) -> ReconciliationResult:
        """Evaluates a 1:1 candidate match identified by Tier 1."""
        
        expected_mdr, expected_gst, _ = calculate_total_fee(gtw.captured_amount, MDR_RATE, GST_RATE)
        expected_net = calculate_expected_net_settlement(
            gtw.captured_amount,
            MDR_RATE,
            GST_RATE,
            refund_amount=gtw.refund_amount,
            chargeback_amount=gtw.chargeback_amount,
        )
        actual_net = bnk.credit_amount - bnk.debit_amount
        
        # If the bank received the EXACT captured amount, fees were 0 (e.g. invoiced separately or EXACT_MATCH scenario)
        if abs(Decimal(str(gtw.captured_amount)) - Decimal(str(actual_net))) <= AMOUNT_TOLERANCE:
            expected_mdr = 0.0
            expected_gst = 0.0
            expected_net = gtw.captured_amount

        difference = round_currency(expected_net - actual_net)
        abs_diff = abs(Decimal(str(difference)))

        # Evidence construction
        erp_ev = build_erp_evidence([erp]) if erp else []
        gtw_ev = build_gateway_evidence([gtw])
        bnk_ev = build_bank_evidence([bnk])
        fin_ev = build_financial_evidence(
            gtw.captured_amount,
            expected_mdr,
            expected_gst,
            expected_net,
            actual_net,
            difference,
            gtw.refund_amount,
            gtw.chargeback_amount,
        )
        
        evidence = ReconciliationEvidence(
            matched_by=matched_by,
            erp_evidence=erp_ev,
            gateway_evidence=gtw_ev,
            bank_evidence=bnk_ev,
            financial_evidence=fin_ev,
        )

        # 2. Determine match type, root cause, and status
        status = ReconciliationStatus.UNRESOLVED
        match_type = MatchType.UNRESOLVED
        root_cause = RootCause.UNKNOWN
        confidence = base_confidence

        if abs_diff <= AMOUNT_TOLERANCE:
            status = ReconciliationStatus.RESOLVED if confidence >= AUTO_RESOLVE_THRESHOLD else ReconciliationStatus.REVIEW
            
            if gtw.chargeback_amount > 0:
                match_type = MatchType.FEE_RECONCILED
                root_cause = RootCause.CHARGEBACK
            elif gtw.refund_amount > 0:
                match_type = MatchType.FEE_RECONCILED
                root_cause = RootCause.REFUND
            elif expected_mdr > 0 or expected_gst > 0:
                match_type = MatchType.FEE_RECONCILED
                root_cause = RootCause.MDR_GST
            else:
                match_type = MatchType.EXACT_1_TO_1
                root_cause = RootCause.EXACT_MATCH
                
        else:
            # Anomaly detection
            # Was an anomalous fee charged?
            actual_fee_charged = gtw.gateway_fee + gtw.gst_on_fee
            expected_total_fee = expected_mdr + expected_gst
            
            if abs(Decimal(str(actual_fee_charged)) - Decimal(str(expected_total_fee))) > AMOUNT_TOLERANCE:
                status = ReconciliationStatus.REVIEW
                match_type = MatchType.FEE_RECONCILED
                root_cause = RootCause.FEE_ANOMALY
                confidence = max(0.75, confidence) # Needs human review but we know what happened
            elif actual_net > 0 and actual_net < expected_net:
                # Partial payout
                status = ReconciliationStatus.REVIEW
                match_type = MatchType.PARTIAL
                root_cause = RootCause.PARTIAL_SETTLEMENT
                confidence = max(0.70, confidence)
            else:
                status = ReconciliationStatus.UNRESOLVED
                match_type = MatchType.UNRESOLVED
                root_cause = RootCause.UNKNOWN
                confidence = min(0.60, confidence)

        explanation = generate_explanation(match_type.value, evidence, expected_net, actual_net, difference)

        return ReconciliationResult(
            reconciliation_id=reconciliation_id,
            status=status,
            match_type=match_type,
            root_cause=root_cause,
            erp_order_ids=[erp.order_id] if erp else [],
            gateway_transaction_ids=[gtw.gateway_transaction_id],
            settlement_id=stl.settlement_id if stl else None,
            bank_transaction_ids=[bnk.bank_transaction_id],
            expected_amount=expected_net,
            actual_amount=actual_net,
            difference=difference,
            confidence=confidence,
            evidence=evidence,
            explanation=explanation,
            recommended_action="Review fee settings" if root_cause == RootCause.FEE_ANOMALY else None
        )
