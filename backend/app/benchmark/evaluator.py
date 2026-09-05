"""Core evaluator: compares engine results against ground truth on a per-case basis.

This is the ONLY module that reads ground truth.
The reconciliation engine has ALREADY completed before this module runs.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

from backend.app.domain.models import GroundTruthCase
from backend.app.reconciliation.types import ReconciliationResult, ReconciliationStatus
from backend.app.benchmark.types import (
    CaseEvaluation,
    EvaluationOutcome,
    FailureReason,
)


class BenchmarkEvaluator:
    """Compares completed engine results against isolated ground truth."""

    def __init__(
        self,
        engine_results: List[ReconciliationResult],
        ground_truth: List[GroundTruthCase],
    ):
        self.engine_results = engine_results
        self.ground_truth = ground_truth

        # Build indexes for fast lookup
        # Index engine results by gateway transaction ID → list of results covering that ID
        self._engine_by_gw_id: Dict[str, List[ReconciliationResult]] = {}
        for r in engine_results:
            for gid in r.gateway_transaction_ids:
                self._engine_by_gw_id.setdefault(gid, []).append(r)

    def evaluate_all(self) -> List[CaseEvaluation]:
        """Evaluates every ground-truth case and returns a list of CaseEvaluations."""
        evaluations: List[CaseEvaluation] = []
        for gt_case in self.ground_truth:
            evaluation = self._evaluate_case(gt_case)
            evaluations.append(evaluation)
        return evaluations

    def _evaluate_case(self, gt: GroundTruthCase) -> CaseEvaluation:
        """Evaluates a single ground-truth case."""
        # Find engine result(s) that cover the ground truth's gateway transactions
        engine_result = self._find_engine_result_for_case(gt)

        # Base evaluation object
        ev = CaseEvaluation(
            case_id=gt.case_id,
            scenario=gt.scenario,
            outcome=EvaluationOutcome.FALSE_NEGATIVE,  # default pessimistic
            gt_erp_order_ids=gt.erp_order_ids,
            gt_gateway_transaction_ids=gt.gateway_transaction_ids,
            gt_settlement_id=gt.settlement_id,
            gt_bank_transaction_ids=gt.bank_transaction_ids,
            gt_expected_relationship=gt.expected_relationship,
            gt_expected_net_amount=gt.expected_net_amount,
            gt_actual_bank_amount=gt.actual_bank_amount,
            gt_root_cause=gt.root_cause,
            gt_is_exception=gt.is_exception,
            financial_value=abs(gt.expected_net_amount),
        )

        if engine_result is None:
            # Engine produced no result for this case's gateway transactions
            ev.outcome = EvaluationOutcome.FALSE_NEGATIVE
            ev.failure_reason = FailureReason.REFERENCE_NOT_FOUND
            ev.failure_detail = f"No engine result covers gateway IDs {gt.gateway_transaction_ids}"
            return ev

        # Populate engine fields
        ev.engine_reconciliation_id = engine_result.reconciliation_id
        ev.engine_status = engine_result.status.value
        ev.engine_match_type = engine_result.match_type.value
        ev.engine_root_cause = engine_result.root_cause.value
        ev.engine_gateway_ids = engine_result.gateway_transaction_ids
        ev.engine_bank_ids = engine_result.bank_transaction_ids
        ev.engine_expected_amount = engine_result.expected_amount
        ev.engine_actual_amount = engine_result.actual_amount
        ev.engine_confidence = engine_result.confidence
        ev.engine_explanation = engine_result.explanation
        ev.financial_impact = engine_result.difference

        # Determine correctness
        ev.outcome = self._classify_outcome(gt, engine_result)

        # If incorrect, determine failure reason
        if ev.outcome in (
            EvaluationOutcome.FALSE_POSITIVE,
            EvaluationOutcome.FALSE_NEGATIVE,
            EvaluationOutcome.INCORRECT_MATCH,
        ):
            ev.failure_reason, ev.failure_detail = self._classify_failure(gt, engine_result)

        return ev

    def _find_engine_result_for_case(self, gt: GroundTruthCase) -> Optional[ReconciliationResult]:
        """Finds the engine result that best covers this ground-truth case.

        Strategy: find an engine result that contains at least one of the ground-truth
        gateway transaction IDs. If multiple results cover different GT gateway IDs,
        prefer the one that covers the most.
        """
        if not gt.gateway_transaction_ids:
            return None

        # Collect all engine results that touch any of the GT gateway IDs
        candidate_results: Dict[str, ReconciliationResult] = {}
        for gid in gt.gateway_transaction_ids:
            for r in self._engine_by_gw_id.get(gid, []):
                candidate_results[r.reconciliation_id] = r

        if not candidate_results:
            return None

        # Pick the result that covers the most GT gateway IDs
        gt_gw_set = set(gt.gateway_transaction_ids)
        best: Optional[ReconciliationResult] = None
        best_overlap = 0

        for r in candidate_results.values():
            overlap = len(gt_gw_set & set(r.gateway_transaction_ids))
            if overlap > best_overlap:
                best = r
                best_overlap = overlap

        return best

    def _classify_outcome(
        self, gt: GroundTruthCase, er: ReconciliationResult
    ) -> EvaluationOutcome:
        """Determines if the engine's decision was correct for this case."""

        # Check structural correctness: do the matched IDs agree?
        relationship_correct = self._check_relationship(gt, er)

        engine_status = er.status

        if gt.is_exception:
            # Ground truth says this IS an exception case
            if engine_status == ReconciliationStatus.RESOLVED:
                if relationship_correct:
                    # Engine resolved an exception case but with correct IDs.
                    # For some exception types (CHARGEBACK, REFUND), resolving correctly
                    # is actually fine if the financial math adds up.
                    # But for MISSING_BANK/MISSING_ERP/DUPLICATE, resolving is wrong.
                    if gt.root_cause in ("MISSING_BANK", "MISSING_ERP", "DUPLICATE"):
                        return EvaluationOutcome.FALSE_POSITIVE
                    else:
                        # CHARGEBACK, PARTIAL_SETTLEMENT, FEE_ANOMALY, REFUND
                        # with correct relationship can be CORRECT_RESOLUTION
                        return EvaluationOutcome.CORRECT_RESOLUTION
                else:
                    return EvaluationOutcome.FALSE_POSITIVE
            elif engine_status == ReconciliationStatus.REVIEW:
                if relationship_correct:
                    return EvaluationOutcome.CORRECT_REVIEW
                else:
                    # Sent to review but with wrong IDs
                    return EvaluationOutcome.INCORRECT_MATCH
            else:  # UNRESOLVED
                # Engine punted entirely on an exception — that's acceptable
                # but we classify it differently from CORRECT_REVIEW
                return EvaluationOutcome.CORRECT_UNRESOLVED
        else:
            # Ground truth says this is NOT an exception (clean reconcilable case)
            if engine_status == ReconciliationStatus.RESOLVED:
                if relationship_correct:
                    return EvaluationOutcome.CORRECT_RESOLUTION
                else:
                    return EvaluationOutcome.INCORRECT_MATCH
            elif engine_status == ReconciliationStatus.REVIEW:
                if relationship_correct:
                    # Correct IDs but engine was conservative — acceptable
                    return EvaluationOutcome.CORRECT_REVIEW
                else:
                    return EvaluationOutcome.INCORRECT_MATCH
            else:  # UNRESOLVED
                return EvaluationOutcome.FALSE_NEGATIVE

    def _check_relationship(self, gt: GroundTruthCase, er: ReconciliationResult) -> bool:
        """Checks if the engine matched the correct set of gateway and bank IDs."""
        gt_gw = set(gt.gateway_transaction_ids)
        er_gw = set(er.gateway_transaction_ids)

        gt_bank = set(gt.bank_transaction_ids)
        er_bank = set(er.bank_transaction_ids)

        # For MISSING_BANK, GT has no bank IDs; engine should also have none
        if gt.expected_relationship == "1_TO_0":
            return gt_gw == er_gw and len(er_bank) == 0

        # For MISSING_ERP (0_TO_1), no ERP in GT but gateway→bank should match
        if gt.expected_relationship == "0_TO_1":
            return gt_gw == er_gw and gt_bank == er_bank

        # For DUPLICATE (1_TO_N), the GT has multiple gateway IDs for one ERP
        # Engine might split them across results. Check that at least the
        # primary gateway ID is correct and bank IDs match.
        if gt.expected_relationship == "1_TO_N":
            # Check if at least the first gateway ID was matched correctly
            return len(gt_gw & er_gw) > 0 and gt_bank == er_bank

        # For UNKNOWN (ambiguous), relationship match is lenient
        if gt.expected_relationship == "UNKNOWN":
            # Any coverage of GT gateway IDs is considered structurally acceptable
            return len(gt_gw & er_gw) > 0

        # Standard 1_TO_1 or N_TO_1
        return gt_gw == er_gw and gt_bank == er_bank

    def _classify_failure(
        self, gt: GroundTruthCase, er: ReconciliationResult
    ) -> Tuple[FailureReason, str]:
        """Evidence-based failure classification."""
        gt_gw = set(gt.gateway_transaction_ids)
        er_gw = set(er.gateway_transaction_ids)
        gt_bank = set(gt.bank_transaction_ids)
        er_bank = set(er.bank_transaction_ids)

        # Wrong bank matched
        if er_bank and gt_bank and er_bank != gt_bank:
            return (
                FailureReason.WRONG_BANK_MATCHED,
                f"Expected bank {gt_bank}, engine matched {er_bank}",
            )

        # Wrong gateway set
        if gt_gw != er_gw:
            missing = gt_gw - er_gw
            extra = er_gw - gt_gw
            if missing:
                return (
                    FailureReason.WRONG_GATEWAY_SET,
                    f"Engine missed gateway IDs: {missing}",
                )
            if extra:
                return (
                    FailureReason.WRONG_GATEWAY_SET,
                    f"Engine included extra gateway IDs: {extra}",
                )

        # Ambiguous scenario
        if gt.scenario == "AMBIGUOUS" or gt.root_cause == "INSUFFICIENT_EVIDENCE":
            return (
                FailureReason.AMBIGUOUS_CANDIDATES,
                "Case is inherently ambiguous with insufficient evidence",
            )

        # Batch with partial coverage
        if gt.expected_relationship == "N_TO_1" and gt_gw != er_gw:
            return (
                FailureReason.BATCH_SEARCH_LIMIT,
                f"Batch match incomplete: expected {len(gt_gw)} gateway txns, got {len(er_gw)}",
            )

        # Missing identifier
        if not er.bank_transaction_ids and gt.bank_transaction_ids:
            return (
                FailureReason.MISSING_IDENTIFIER,
                "Engine could not find matching bank transaction",
            )

        return (FailureReason.OTHER, "Could not determine specific failure reason")
