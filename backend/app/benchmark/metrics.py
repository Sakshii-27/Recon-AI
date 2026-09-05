"""Metrics computation for benchmark evaluation.

All metrics are computed dynamically from CaseEvaluation lists.
No hardcoded expected percentages.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List

from backend.app.benchmark.types import CaseEvaluation, EvaluationOutcome


def _safe_divide(numerator: float, denominator: float) -> float:
    """Safe division returning 0.0 when denominator is zero."""
    if denominator == 0:
        return 0.0
    return float(Decimal(str(numerator)) / Decimal(str(denominator)))


def _pct(numerator: float, denominator: float) -> float:
    """Percentage, rounded to 2 decimal places."""
    if denominator == 0:
        return 0.0
    raw = (Decimal(str(numerator)) / Decimal(str(denominator))) * 100
    return float(raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def compute_accuracy_metrics(evaluations: List[CaseEvaluation]) -> Dict[str, Any]:
    """Computes precision, recall, F1, and match rate."""
    total = len(evaluations)
    if total == 0:
        return {
            "total_cases": 0,
            "correct_count": 0,
            "incorrect_count": 0,
            "false_positive_count": 0,
            "false_negative_count": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1_score": 0.0,
            "match_rate": 0.0,
        }

    correct = sum(
        1 for e in evaluations if e.outcome in (
            EvaluationOutcome.CORRECT_RESOLUTION,
            EvaluationOutcome.CORRECT_REVIEW,
            EvaluationOutcome.CORRECT_UNRESOLVED,
        )
    )
    incorrect = sum(
        1 for e in evaluations if e.outcome == EvaluationOutcome.INCORRECT_MATCH
    )
    false_positives = sum(
        1 for e in evaluations if e.outcome == EvaluationOutcome.FALSE_POSITIVE
    )
    false_negatives = sum(
        1 for e in evaluations if e.outcome == EvaluationOutcome.FALSE_NEGATIVE
    )

    # True positives = cases where engine resolved/reviewed correctly
    # For precision/recall in reconciliation:
    #   TP = correctly resolved OR correctly reviewed (engine acted and was right)
    #   FP = false positives (engine resolved but was wrong)
    #   FN = false negatives (engine missed a valid case)
    tp = sum(
        1 for e in evaluations if e.outcome in (
            EvaluationOutcome.CORRECT_RESOLUTION,
            EvaluationOutcome.CORRECT_REVIEW,
        )
    )

    precision = _pct(tp, tp + false_positives)
    recall = _pct(tp, tp + false_negatives)
    f1 = 0.0
    if precision + recall > 0:
        f1 = float(
            (Decimal("2") * Decimal(str(precision)) * Decimal(str(recall))
             / (Decimal(str(precision)) + Decimal(str(recall))))
            .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

    # Match rate: correctly reconciled (resolved) / total reconcilable
    # A reconcilable case is one where ground truth says it's NOT an exception
    # OR it's an exception that CAN be correctly identified (all cases except AMBIGUOUS with UNKNOWN relationship)
    reconcilable = [
        e for e in evaluations
        if not (e.gt_expected_relationship == "UNKNOWN")
    ]
    correctly_reconciled = sum(
        1 for e in reconcilable
        if e.outcome in (EvaluationOutcome.CORRECT_RESOLUTION, EvaluationOutcome.CORRECT_REVIEW)
    )
    match_rate = _pct(correctly_reconciled, len(reconcilable)) if reconcilable else 0.0

    return {
        "total_cases": total,
        "correct_count": correct,
        "incorrect_count": incorrect,
        "false_positive_count": false_positives,
        "false_negative_count": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "match_rate": match_rate,
    }


def compute_financial_metrics(evaluations: List[CaseEvaluation]) -> Dict[str, Any]:
    """Computes financial value reconciliation metrics using Decimal arithmetic."""
    total_expected = Decimal("0")
    total_actual_bank = Decimal("0")
    correctly_reconciled_value = Decimal("0")
    unreconciled_value = Decimal("0")
    false_positive_value = Decimal("0")
    false_negative_value = Decimal("0")
    unresolved_value = Decimal("0")

    for e in evaluations:
        case_value = Decimal(str(abs(e.gt_expected_net_amount)))
        total_expected += case_value

        if e.gt_actual_bank_amount is not None:
            total_actual_bank += Decimal(str(abs(e.gt_actual_bank_amount)))

        if e.outcome in (
            EvaluationOutcome.CORRECT_RESOLUTION,
            EvaluationOutcome.CORRECT_REVIEW,
        ):
            correctly_reconciled_value += case_value
        elif e.outcome == EvaluationOutcome.FALSE_POSITIVE:
            false_positive_value += case_value
        elif e.outcome == EvaluationOutcome.FALSE_NEGATIVE:
            false_negative_value += case_value
            unreconciled_value += case_value
        elif e.outcome == EvaluationOutcome.INCORRECT_MATCH:
            unreconciled_value += case_value
        elif e.outcome == EvaluationOutcome.CORRECT_UNRESOLVED:
            unresolved_value += case_value

    value_pct = _pct(float(correctly_reconciled_value), float(total_expected))

    return {
        "total_expected_value": float(total_expected),
        "total_actual_bank_value": float(total_actual_bank),
        "correctly_reconciled_value": float(correctly_reconciled_value),
        "value_reconciliation_percentage": value_pct,
        "unreconciled_value": float(unreconciled_value),
        "false_positive_financial_value": float(false_positive_value),
        "false_negative_financial_value": float(false_negative_value),
        "unresolved_financial_value": float(unresolved_value),
    }


def compute_decision_metrics(evaluations: List[CaseEvaluation]) -> Dict[str, int]:
    """Counts engine decisions by status."""
    resolved = sum(1 for e in evaluations if e.engine_status == "RESOLVED")
    review = sum(1 for e in evaluations if e.engine_status == "REVIEW")
    unresolved = sum(
        1 for e in evaluations
        if e.engine_status == "UNRESOLVED" or e.engine_status is None
    )
    return {
        "resolved": resolved,
        "review": review,
        "unresolved": unresolved,
    }


def compute_review_quality(evaluations: List[CaseEvaluation]) -> Dict[str, Any]:
    """Measures quality of REVIEW decisions."""
    review_cases = [e for e in evaluations if e.engine_status == "REVIEW"]
    review_count = len(review_cases)
    correct_review = sum(
        1 for e in review_cases
        if e.outcome in (EvaluationOutcome.CORRECT_REVIEW,)
    )
    incorrect_review = review_count - correct_review

    return {
        "review_count": review_count,
        "correct_review_count": correct_review,
        "incorrect_review_count": incorrect_review,
        "review_precision": _pct(correct_review, review_count),
        "review_rate": _pct(review_count, len(evaluations)) if evaluations else 0.0,
    }


def compute_autonomous_resolution(evaluations: List[CaseEvaluation]) -> Dict[str, Any]:
    """Measures safe_autonomous_resolution_rate:
    correct autonomous resolutions / all autonomous resolutions.
    Where 'autonomous' = engine chose RESOLVED.
    """
    autonomous = [e for e in evaluations if e.engine_status == "RESOLVED"]
    correct_autonomous = sum(
        1 for e in autonomous
        if e.outcome == EvaluationOutcome.CORRECT_RESOLUTION
    )
    total_autonomous = len(autonomous)

    return {
        "total_autonomous_resolutions": total_autonomous,
        "correct_autonomous_resolutions": correct_autonomous,
        "safe_autonomous_resolution_rate": _pct(correct_autonomous, total_autonomous),
    }
