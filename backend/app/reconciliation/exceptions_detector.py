"""Exception Detector for unmatched stragglers."""

from typing import Dict, List, Tuple

from backend.app.domain.finance_rules import calculate_expected_net_settlement, calculate_total_fee
from backend.app.domain.models import BankTransaction, ERPOrder, GatewaySettlement, GatewayTransaction
from backend.app.reconciliation.config import GST_RATE, MDR_RATE
from backend.app.reconciliation.evidence import (
    build_bank_evidence,
    build_erp_evidence,
    build_financial_evidence,
    build_gateway_evidence,
    generate_explanation,
)
from backend.app.reconciliation.state import ReconciliationState
from backend.app.reconciliation.types import (
    MatchType,
    ReconciliationEvidence,
    ReconciliationResult,
    ReconciliationStatus,
    RootCause,
)


class ExceptionsDetector:
    """Detects explicit exceptions like MISSING_BANK, MISSING_ERP, DUPLICATES, etc."""

    def __init__(self, state: ReconciliationState):
        self.state = state

    def run(
        self,
        erp_orders: List[ERPOrder],
        gateway_txns: List[GatewayTransaction],
        settlements: List[GatewaySettlement],
        bank_txns: List[BankTransaction],
        reconciliation_id_counter: int
    ) -> Tuple[List[ReconciliationResult], int]:
        results = []
        
        erp_by_ref = {e.order_reference: e for e in erp_orders}

        # 1. Missing ERP / Missing Bank / Duplicates from Gateway's perspective
        # A duplicate is when 2 gateway txns have the same order ref, and one is already matched or both are unmatched.
        # For simplicity, if a gateway transaction is unmatched and it has no ERP order, it's MISSING_ERP.
        # If it has a settlement ID and that settlement is not in bank, it's MISSING_BANK.
        
        for gtw in gateway_txns:
            if not self.state.is_gateway_available(gtw.gateway_transaction_id):
                continue

            erp = erp_by_ref.get(gtw.order_reference)
            stl = next((s for s in settlements if s.settlement_id == gtw.settlement_id), None)
            
            # Identify root cause
            root_cause = RootCause.UNKNOWN
            match_type = MatchType.UNRESOLVED
            status = ReconciliationStatus.UNRESOLVED
            
            # Check for duplicate: if ERP is found but already used by another gateway transaction
            if erp and not self.state.is_erp_available(erp.order_id):
                root_cause = RootCause.DUPLICATE
                match_type = MatchType.DUPLICATE
                status = ReconciliationStatus.REVIEW
                # We do not mark ERP as available because it is already consumed, we just reference it in evidence
                erp = None 
            elif not erp:
                root_cause = RootCause.MISSING_ERP
                match_type = MatchType.MISSING_ERP
                status = ReconciliationStatus.REVIEW
            elif stl and gtw.settlement_id:
                # If the transaction was batched, we check if the entire settlement is missing.
                # In this simpler detector, if a transaction is still available, and its settlement wasn't matched,
                # it's highly likely a missing bank deposit.
                root_cause = RootCause.MISSING_BANK
                match_type = MatchType.MISSING_BANK
                status = ReconciliationStatus.REVIEW

            mdr, gst, _ = calculate_total_fee(gtw.captured_amount, MDR_RATE, GST_RATE)
            expected_net = calculate_expected_net_settlement(
                gtw.captured_amount, MDR_RATE, GST_RATE,
                refund_amount=gtw.refund_amount, chargeback_amount=gtw.chargeback_amount
            )

            erp_ev = build_erp_evidence([erp]) if erp else []
            gtw_ev = build_gateway_evidence([gtw])
            fin_ev = build_financial_evidence(
                gtw.captured_amount, mdr, gst, expected_net, 0.0, expected_net, gtw.refund_amount, gtw.chargeback_amount
            )

            evidence = ReconciliationEvidence(
                matched_by=["exception_detector"],
                erp_evidence=erp_ev,
                gateway_evidence=gtw_ev,
                bank_evidence=[],
                financial_evidence=fin_ev,
            )

            explanation = generate_explanation(match_type.value, evidence, expected_net, 0.0, expected_net)

            res = ReconciliationResult(
                reconciliation_id=f"REC-{reconciliation_id_counter:05d}",
                status=status,
                match_type=match_type,
                root_cause=root_cause,
                erp_order_ids=[erp.order_id] if erp else [],
                gateway_transaction_ids=[gtw.gateway_transaction_id],
                settlement_id=gtw.settlement_id,
                bank_transaction_ids=[],
                expected_amount=expected_net,
                actual_amount=0.0,
                difference=expected_net,
                confidence=0.99, # Deterministically confident in the exception
                evidence=evidence,
                explanation=explanation,
            )
            
            results.append(res)
            reconciliation_id_counter += 1
            
            self.state.mark_reconciled(
                [erp.order_id] if erp else [],
                [gtw.gateway_transaction_id],
                gtw.settlement_id,
                []
            )

        return results, reconciliation_id_counter
