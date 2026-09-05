"""Main Deterministic Reconciliation Engine Orchestrator."""

import time
from typing import Dict, List, Any

from backend.app.domain.models import BankTransaction, ERPOrder, GatewaySettlement, GatewayTransaction
from backend.app.reconciliation.exceptions_detector import ExceptionsDetector
from backend.app.reconciliation.state import ReconciliationState
from backend.app.reconciliation.tier1_matcher import Tier1Matcher
from backend.app.reconciliation.tier2_financial import Tier2FinancialValidator
from backend.app.reconciliation.tier3_batch import Tier3BatchMatcher
from backend.app.reconciliation.types import MatchType, ReconciliationResult, ReconciliationStatus, RootCause


class ReconciliationEngine:
    """The Autonomous Deterministic Finance Reconciliation Engine."""

    def __init__(self):
        pass

    def reconcile(
        self,
        erp_orders: List[ERPOrder],
        gateway_txns: List[GatewayTransaction],
        settlements: List[GatewaySettlement],
        bank_txns: List[BankTransaction],
    ) -> Dict[str, Any]:
        """Runs the deterministic multi-tier reconciliation pipeline."""
        start_time = time.time()
        
        state = ReconciliationState()
        results: List[ReconciliationResult] = []
        rec_id_counter = 1
        
        # 1. Tier 1: Exact 1:1 Matching
        t1_matcher = Tier1Matcher(state)
        t1_candidates = t1_matcher.run(erp_orders, gateway_txns, settlements, bank_txns)
        
        # 2. Tier 2: Financial Validation of 1:1 Matches
        t2_validator = Tier2FinancialValidator()
        for erp, gtw, stl, bnk, conf, evidence in t1_candidates:
            res = t2_validator.evaluate_1_to_1_match(
                erp, gtw, stl, bnk, conf, evidence, f"REC-{rec_id_counter:05d}"
            )
            results.append(res)
            rec_id_counter += 1
            
        # 3. Tier 3: N:1 Batch Settlement Matching
        t3_matcher = Tier3BatchMatcher(state)
        batch_results, rec_id_counter = t3_matcher.run(
            erp_orders, gateway_txns, settlements, bank_txns, rec_id_counter
        )
        results.extend(batch_results)

        # 4. Exception Detection (Stragglers)
        detector = ExceptionsDetector(state)
        exc_results, rec_id_counter = detector.run(
            erp_orders, gateway_txns, settlements, bank_txns, rec_id_counter
        )
        results.extend(exc_results)

        # 5. Compile Summary Metrics
        elapsed_ms = (time.time() - start_time) * 1000.0
        
        resolved_count = sum(1 for r in results if r.status == ReconciliationStatus.RESOLVED)
        review_count = sum(1 for r in results if r.status == ReconciliationStatus.REVIEW)
        unresolved_count = sum(1 for r in results if r.status == ReconciliationStatus.UNRESOLVED)

        exact_match_count = sum(1 for r in results if r.match_type == MatchType.EXACT_1_TO_1)
        fee_reconciled_count = sum(1 for r in results if r.match_type == MatchType.FEE_RECONCILED)
        batch_match_count = sum(1 for r in results if r.match_type == MatchType.BATCH_N_TO_1)
        missing_bank_count = sum(1 for r in results if r.root_cause == RootCause.MISSING_BANK)
        missing_erp_count = sum(1 for r in results if r.root_cause == RootCause.MISSING_ERP)
        duplicate_count = sum(1 for r in results if r.root_cause == RootCause.DUPLICATE)

        total_expected_value = sum(r.expected_amount for r in results)
        total_actual_value = sum(r.actual_amount for r in results)
        total_difference = sum(r.difference for r in results)
        
        # Exposure is any positive difference where status is not completely resolved.
        # Even if resolved, missing money is technically exposure if it's an anomaly or partial.
        unresolved_exposure = sum(r.difference for r in results if r.status != ReconciliationStatus.RESOLVED and r.difference > 0)

        summary = {
            "records_processed": len(gateway_txns),
            "resolved_count": resolved_count,
            "review_count": review_count,
            "unresolved_count": unresolved_count,
            "exact_match_count": exact_match_count,
            "fee_reconciled_count": fee_reconciled_count,
            "batch_match_count": batch_match_count,
            "missing_bank_count": missing_bank_count,
            "missing_erp_count": missing_erp_count,
            "duplicate_count": duplicate_count,
            "total_expected_value": total_expected_value,
            "total_actual_value": total_actual_value,
            "total_difference": total_difference,
            "total_unresolved_value": unresolved_exposure,
            "processing_time_ms": elapsed_ms,
        }

        exceptions = [r for r in results if r.status != ReconciliationStatus.RESOLVED]

        return {
            "reconciliation_results": results,
            "exceptions": exceptions,
            "summary": summary,
        }
