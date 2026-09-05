"""Tier 1: Deterministic 1:1 Matching rules."""

from typing import Dict, List, Optional, Tuple

from backend.app.domain.models import BankTransaction, ERPOrder, GatewaySettlement, GatewayTransaction
from backend.app.reconciliation.normalizer import contains_id_in_narration
from backend.app.reconciliation.state import ReconciliationState


class Tier1Matcher:
    """Executes deterministic 1:1 matching based on explicit identifiers."""

    def __init__(self, state: ReconciliationState):
        self.state = state

    def run(
        self,
        erp_orders: List[ERPOrder],
        gateway_txns: List[GatewayTransaction],
        settlements: List[GatewaySettlement],
        bank_txns: List[BankTransaction],
    ) -> List[Tuple[Optional[ERPOrder], GatewayTransaction, Optional[GatewaySettlement], BankTransaction, float, List[str]]]:
        """
        Returns a list of tuples: (ERPOrder, GatewayTransaction, GatewaySettlement, BankTransaction, confidence, match_evidence_list)
        Only exactly 1:1 matched tuples are returned.
        """
        results = []

        # Indexes for fast lookup
        erp_by_ref = {e.order_reference: e for e in erp_orders}
        stl_by_id = {s.settlement_id: s for s in settlements}

        # Iterating over gateway transactions to find 1:1 bank matches
        for gtw in gateway_txns:
            if not self.state.is_gateway_available(gtw.gateway_transaction_id):
                continue

            matched_bank: Optional[BankTransaction] = None
            evidence_used = []
            confidence = 0.0

            # Find matching bank transaction
            for bnk in bank_txns:
                if not self.state.is_bank_available(bnk.bank_transaction_id):
                    continue

                # 1. Exact Gateway ID in bank narration
                if contains_id_in_narration(bnk.description, gtw.gateway_transaction_id):
                    matched_bank = bnk
                    evidence_used.append("exact_gateway_transaction_id_in_narration")
                    confidence = 1.00
                    break

                # 2. Exact Settlement ID in bank narration / reference (if this is a 1:1 settlement)
                if gtw.settlement_id:
                    stl = stl_by_id.get(gtw.settlement_id)
                    # Check if settlement is 1:1 (i.e. only one gateway transaction in it)
                    if stl and len(stl.transaction_ids) == 1 and self.state.is_settlement_available(stl.settlement_id):
                        if (contains_id_in_narration(bnk.description, stl.settlement_id) or 
                            contains_id_in_narration(bnk.reference, stl.settlement_id)):
                            matched_bank = bnk
                            evidence_used.append("exact_settlement_id")
                            confidence = 0.99
                            break

                # 3. Exact UTR matching (if gateway provides UTR, though our model might not track gateway UTR directly, 
                # but if we could cross-ref, this is where it'd go. Instead, match Order Ref in bank narration)
                if contains_id_in_narration(bnk.description, gtw.order_reference) or \
                   contains_id_in_narration(bnk.reference, gtw.order_reference):
                    # To prevent false positives, also check if date is within window and amount is exact/expected net
                    # But if the reference is truly unique, it's strong.
                    # We will assign 0.90 confidence and verify financials in Tier 2.
                    matched_bank = bnk
                    evidence_used.append("exact_order_reference")
                    confidence = 0.90
                    break

            if matched_bank:
                erp = erp_by_ref.get(gtw.order_reference)
                if erp and not self.state.is_erp_available(erp.order_id):
                    erp = None # Already used
                
                stl = stl_by_id.get(gtw.settlement_id) if gtw.settlement_id else None
                if stl and not self.state.is_settlement_available(stl.settlement_id):
                    stl = None
                
                # Mark used
                erp_ids = [erp.order_id] if erp else []
                stl_id = stl.settlement_id if stl else None
                self.state.mark_reconciled(erp_ids, [gtw.gateway_transaction_id], stl_id, [matched_bank.bank_transaction_id])
                
                results.append((erp, gtw, stl, matched_bank, confidence, evidence_used))

        return results
