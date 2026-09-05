"""Per-scenario and per-match-type metric calculations."""

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List

from backend.app.benchmark.types import (
    CaseEvaluation,
    EvaluationOutcome,
    MatchTypeMetrics,
    ScenarioMetrics,
)
from backend.app.benchmark.metrics import _pct


# All known scenario names (including UNKNOWN for future-proofing)
ALL_SCENARIOS = [
    "EXACT_MATCH", "MDR_GST", "T_PLUS_1", "T_PLUS_2",
    "BATCH_SETTLEMENT", "REFUND", "CHARGEBACK", "PARTIAL_SETTLEMENT",
    "DUPLICATE", "MISSING_BANK", "MISSING_ERP", "FEE_ANOMALY",
    "AMBIGUOUS", "UNKNOWN",
]


def compute_scenario_metrics(evaluations: List[CaseEvaluation]) -> Dict[str, Any]:
    """Computes per-scenario performance metrics."""
    by_scenario: Dict[str, List[CaseEvaluation]] = defaultdict(list)
    for e in evaluations:
        by_scenario[e.scenario].append(e)

    result: Dict[str, Any] = {}

    for scenario in ALL_SCENARIOS:
        cases = by_scenario.get(scenario, [])
        total = len(cases)
        if total == 0:
            result[scenario] = ScenarioMetrics(scenario=scenario).model_dump()
            continue

        correct = sum(
            1 for e in cases if e.outcome in (
                EvaluationOutcome.CORRECT_RESOLUTION,
                EvaluationOutcome.CORRECT_REVIEW,
                EvaluationOutcome.CORRECT_UNRESOLVED,
            )
        )
        incorrect = sum(
            1 for e in cases if e.outcome == EvaluationOutcome.INCORRECT_MATCH
        )
        fp = sum(1 for e in cases if e.outcome == EvaluationOutcome.FALSE_POSITIVE)
        fn = sum(1 for e in cases if e.outcome == EvaluationOutcome.FALSE_NEGATIVE)

        resolved = sum(1 for e in cases if e.engine_status == "RESOLVED")
        review = sum(1 for e in cases if e.engine_status == "REVIEW")
        unresolved = sum(
            1 for e in cases if e.engine_status == "UNRESOLVED" or e.engine_status is None
        )

        # Precision: TP / (TP + FP) for this scenario
        tp = sum(
            1 for e in cases if e.outcome in (
                EvaluationOutcome.CORRECT_RESOLUTION,
                EvaluationOutcome.CORRECT_REVIEW,
            )
        )
        precision = _pct(tp, tp + fp)
        recall = _pct(tp, tp + fn)
        match_rate = _pct(correct, total)

        value_total = float(sum(Decimal(str(abs(e.gt_expected_net_amount))) for e in cases))
        value_reconciled = float(sum(
            Decimal(str(abs(e.gt_expected_net_amount)))
            for e in cases
            if e.outcome in (EvaluationOutcome.CORRECT_RESOLUTION, EvaluationOutcome.CORRECT_REVIEW)
        ))
        value_pct = _pct(value_reconciled, value_total) if value_total > 0 else 0.0

        sm = ScenarioMetrics(
            scenario=scenario,
            total_cases=total,
            correct=correct,
            incorrect=incorrect,
            resolved=resolved,
            review=review,
            unresolved=unresolved,
            false_positives=fp,
            false_negatives=fn,
            precision=precision,
            recall=recall,
            match_rate=match_rate,
            value_reconciled=value_reconciled,
            value_total=value_total,
            value_reconciliation_percentage=value_pct,
        )
        result[scenario] = sm.model_dump()

    return result


def compute_match_type_metrics(evaluations: List[CaseEvaluation]) -> Dict[str, Any]:
    """Computes per-match-type performance metrics."""
    by_match_type: Dict[str, List[CaseEvaluation]] = defaultdict(list)
    for e in evaluations:
        mt = e.engine_match_type or "UNMATCHED"
        by_match_type[mt].append(e)

    result: Dict[str, Any] = {}
    for mt, cases in by_match_type.items():
        count = len(cases)
        correct = sum(
            1 for e in cases if e.outcome in (
                EvaluationOutcome.CORRECT_RESOLUTION,
                EvaluationOutcome.CORRECT_REVIEW,
                EvaluationOutcome.CORRECT_UNRESOLVED,
            )
        )
        incorrect = count - correct
        value = float(sum(Decimal(str(abs(e.gt_expected_net_amount))) for e in cases))
        accuracy = _pct(correct, count)

        mtm = MatchTypeMetrics(
            match_type=mt,
            count=count,
            correct=correct,
            incorrect=incorrect,
            financial_value=value,
            accuracy=accuracy,
        )
        result[mt] = mtm.model_dump()

    return result
