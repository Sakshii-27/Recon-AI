"""Comprehensive test suite for the Recon-AI Benchmark & Evaluation Suite (Phase 3).

Tests cover:
- Ground truth isolation enforcement
- Structural integrity checks
- Metric calculations (precision, recall, F1, match rate, financial)
- Per-scenario metrics
- False positive / false negative detection
- Review classification
- Reproducibility
- Decimal financial math
- Edge cases (zero matches, all correct, all unresolved, etc.)
- Benchmark output schema validation
- 100 / 500 / 1000 record benchmarks
"""

import json
import sys
import time
from decimal import Decimal
from pathlib import Path
from typing import List

import pytest

from backend.app.data_generation.generator import SyntheticDataGenerator
from backend.app.domain.models import GroundTruthCase
from backend.app.reconciliation.engine import ReconciliationEngine
from backend.app.reconciliation.types import (
    MatchType,
    ReconciliationEvidence,
    ReconciliationResult,
    ReconciliationStatus,
    RootCause,
)
from backend.app.benchmark.evaluator import BenchmarkEvaluator
from backend.app.benchmark.types import (
    BenchmarkReport,
    CaseEvaluation,
    EvaluationOutcome,
    FailureReason,
)
from backend.app.benchmark.metrics import (
    compute_accuracy_metrics,
    compute_autonomous_resolution,
    compute_decision_metrics,
    compute_financial_metrics,
    compute_review_quality,
)
from backend.app.benchmark.scenario_metrics import (
    compute_match_type_metrics,
    compute_scenario_metrics,
)
from backend.app.benchmark.reporter import build_report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_engine(records: int, seed: int = 42):
    """Generates data and runs the Phase 2 engine. Returns (engine_results, ground_truth, dataset_counts)."""
    gen = SyntheticDataGenerator(seed=seed)
    erp, gtw, stl, bnk, gt = gen.generate_dataset(records)
    engine = ReconciliationEngine()
    output = engine.reconcile(erp, gtw, stl, bnk)
    dataset_counts = {
        "erp_records": len(erp),
        "gateway_transactions": len(gtw),
        "gateway_settlements": len(stl),
        "bank_transactions": len(bnk),
    }
    return output["reconciliation_results"], gt, dataset_counts


def _make_dummy_result(
    rec_id="REC-T1",
    status=ReconciliationStatus.RESOLVED,
    match_type=MatchType.EXACT_1_TO_1,
    root_cause=RootCause.EXACT_MATCH,
    gw_ids=None,
    bank_ids=None,
    expected=1000.0,
    actual=1000.0,
    confidence=1.0,
) -> ReconciliationResult:
    return ReconciliationResult(
        reconciliation_id=rec_id,
        status=status,
        match_type=match_type,
        root_cause=root_cause,
        erp_order_ids=["ORD-1"],
        gateway_transaction_ids=gw_ids or ["TXN-1"],
        settlement_id="SET-1",
        bank_transaction_ids=bank_ids or ["BANK-1"],
        expected_amount=expected,
        actual_amount=actual,
        difference=expected - actual,
        confidence=confidence,
        evidence=ReconciliationEvidence(matched_by=["test"]),
        explanation="Test",
    )


def _make_dummy_gt(
    case_id="CASE-T1",
    scenario="EXACT_MATCH",
    gw_ids=None,
    bank_ids=None,
    relationship="1_TO_1",
    expected_net=1000.0,
    actual_bank=1000.0,
    root_cause=None,
    is_exception=False,
) -> GroundTruthCase:
    return GroundTruthCase(
        case_id=case_id,
        scenario=scenario,
        erp_order_ids=["ORD-1"],
        gateway_transaction_ids=gw_ids or ["TXN-1"],
        settlement_id="SET-1",
        bank_transaction_ids=bank_ids or ["BANK-1"],
        expected_relationship=relationship,
        expected_net_amount=expected_net,
        actual_bank_amount=actual_bank,
        root_cause=root_cause,
        is_exception=is_exception,
        description="Test case",
    )


# ===========================================================================
# 1. GROUND TRUTH ISOLATION
# ===========================================================================

class TestGroundTruthIsolation:

    def test_benchmark_does_not_modify_engine(self):
        """The engine code must not be changed by running the benchmark."""
        import importlib
        mod_before = importlib.import_module("backend.app.reconciliation.engine")
        source_before = Path(mod_before.__file__).read_text()

        # Run benchmark
        results, gt, _ = _run_engine(20)
        evaluator = BenchmarkEvaluator(results, gt)
        evaluator.evaluate_all()

        source_after = Path(mod_before.__file__).read_text()
        assert source_before == source_after

    def test_ground_truth_not_passed_to_engine(self):
        """ReconciliationEngine.reconcile() does not accept ground truth."""
        import inspect
        sig = inspect.signature(ReconciliationEngine.reconcile)
        params = list(sig.parameters.keys())
        for p in params:
            assert "ground_truth" not in p.lower()
            assert "truth" not in p.lower()

    def test_ground_truth_is_evaluator_only(self):
        """The reconciliation package has no import of ground truth."""
        import ast
        recon_dir = Path("backend/app/reconciliation")
        for py_file in recon_dir.glob("*.py"):
            source = py_file.read_text()
            assert "ground_truth" not in source.lower(), \
                f"{py_file.name} references ground_truth"
            assert "GroundTruthCase" not in source, \
                f"{py_file.name} imports GroundTruthCase"

    def test_dependency_direction(self):
        """benchmark → reconciliation is allowed; reconciliation → benchmark is NOT."""
        recon_dir = Path("backend/app/reconciliation")
        for py_file in recon_dir.glob("*.py"):
            source = py_file.read_text()
            assert "benchmark" not in source, \
                f"{py_file.name} imports from benchmark package"


# ===========================================================================
# 2. METRIC CALCULATIONS
# ===========================================================================

class TestPrecisionCalculation:

    def test_precision_all_correct(self):
        """100% precision when all are correct resolutions."""
        er = _make_dummy_result()
        gt = _make_dummy_gt()
        evaluator = BenchmarkEvaluator([er], [gt])
        evals = evaluator.evaluate_all()
        metrics = compute_accuracy_metrics(evals)
        assert metrics["precision"] == 100.0

    def test_precision_with_false_positive(self):
        """Precision drops with false positives."""
        # Correct case
        er1 = _make_dummy_result(rec_id="R1", gw_ids=["TXN-1"], bank_ids=["BANK-1"])
        gt1 = _make_dummy_gt(case_id="C1", gw_ids=["TXN-1"], bank_ids=["BANK-1"])

        # False positive: engine resolved but wrong bank
        er2 = _make_dummy_result(rec_id="R2", gw_ids=["TXN-2"], bank_ids=["BANK-WRONG"])
        gt2 = _make_dummy_gt(
            case_id="C2", gw_ids=["TXN-2"], bank_ids=["BANK-2"],
            root_cause="MISSING_BANK", is_exception=True, relationship="1_TO_0",
            actual_bank=None,
        )

        evaluator = BenchmarkEvaluator([er1, er2], [gt1, gt2])
        evals = evaluator.evaluate_all()
        metrics = compute_accuracy_metrics(evals)
        assert metrics["precision"] < 100.0
        assert metrics["false_positive_count"] >= 1


class TestRecallCalculation:

    def test_recall_all_found(self):
        """100% recall when no false negatives."""
        er = _make_dummy_result()
        gt = _make_dummy_gt()
        evaluator = BenchmarkEvaluator([er], [gt])
        evals = evaluator.evaluate_all()
        metrics = compute_accuracy_metrics(evals)
        assert metrics["recall"] == 100.0

    def test_recall_with_false_negative(self):
        """Recall drops when engine misses a case."""
        # Engine produced nothing for this case
        gt = _make_dummy_gt(case_id="C1", gw_ids=["TXN-MISSING"])
        evaluator = BenchmarkEvaluator([], [gt])
        evals = evaluator.evaluate_all()
        metrics = compute_accuracy_metrics(evals)
        assert metrics["recall"] == 0.0
        assert metrics["false_negative_count"] == 1


class TestF1Calculation:

    def test_f1_perfect(self):
        er = _make_dummy_result()
        gt = _make_dummy_gt()
        evaluator = BenchmarkEvaluator([er], [gt])
        evals = evaluator.evaluate_all()
        metrics = compute_accuracy_metrics(evals)
        assert metrics["f1_score"] == 100.0

    def test_f1_zero_when_all_wrong(self):
        gt = _make_dummy_gt(case_id="C1", gw_ids=["TXN-MISSING"])
        evaluator = BenchmarkEvaluator([], [gt])
        evals = evaluator.evaluate_all()
        metrics = compute_accuracy_metrics(evals)
        assert metrics["f1_score"] == 0.0


class TestMatchRateCalculation:

    def test_match_rate_calculation(self):
        er = _make_dummy_result()
        gt = _make_dummy_gt()
        evaluator = BenchmarkEvaluator([er], [gt])
        evals = evaluator.evaluate_all()
        metrics = compute_accuracy_metrics(evals)
        assert metrics["match_rate"] > 0


class TestValueReconciliationCalculation:

    def test_value_reconciliation(self):
        er = _make_dummy_result(expected=5000.0, actual=5000.0)
        gt = _make_dummy_gt(expected_net=5000.0, actual_bank=5000.0)
        evaluator = BenchmarkEvaluator([er], [gt])
        evals = evaluator.evaluate_all()
        fin = compute_financial_metrics(evals)
        assert fin["total_expected_value"] == 5000.0
        assert fin["correctly_reconciled_value"] == 5000.0
        assert fin["value_reconciliation_percentage"] == 100.0


class TestDecimalFinancialMath:

    def test_no_floating_point_drift(self):
        """Financial metrics must use Decimal internally to avoid float drift."""
        evals = []
        for i in range(100):
            ev = CaseEvaluation(
                case_id=f"C-{i}",
                scenario="EXACT_MATCH",
                outcome=EvaluationOutcome.CORRECT_RESOLUTION,
                gt_expected_net_amount=99.99,
                gt_actual_bank_amount=99.99,
                financial_value=99.99,
                engine_status="RESOLVED",
            )
            evals.append(ev)

        fin = compute_financial_metrics(evals)
        # 100 * 99.99 = 9999.00 exactly
        assert fin["total_expected_value"] == 9999.0
        assert fin["correctly_reconciled_value"] == 9999.0


# ===========================================================================
# 3. FALSE POSITIVE / FALSE NEGATIVE DETECTION
# ===========================================================================

class TestFalsePositiveDetection:

    def test_false_positive_on_missing_bank_resolved(self):
        """If GT says MISSING_BANK but engine says RESOLVED, that's a false positive."""
        er = _make_dummy_result(gw_ids=["TXN-1"], bank_ids=["BANK-1"])
        gt = _make_dummy_gt(
            gw_ids=["TXN-1"], bank_ids=[], relationship="1_TO_0",
            root_cause="MISSING_BANK", is_exception=True, actual_bank=None,
        )
        evaluator = BenchmarkEvaluator([er], [gt])
        evals = evaluator.evaluate_all()
        assert evals[0].outcome == EvaluationOutcome.FALSE_POSITIVE


class TestFalseNegativeDetection:

    def test_false_negative_when_no_engine_result(self):
        """If engine produces nothing for a valid case, that's a false negative."""
        gt = _make_dummy_gt(gw_ids=["TXN-ORPHAN"])
        evaluator = BenchmarkEvaluator([], [gt])
        evals = evaluator.evaluate_all()
        assert evals[0].outcome == EvaluationOutcome.FALSE_NEGATIVE
        assert evals[0].failure_reason == FailureReason.REFERENCE_NOT_FOUND


class TestReviewClassification:

    def test_correct_review_for_ambiguous(self):
        """An AMBIGUOUS case sent to REVIEW is a correct conservative decision."""
        er = _make_dummy_result(
            status=ReconciliationStatus.REVIEW,
            match_type=MatchType.UNRESOLVED,
            root_cause=RootCause.UNKNOWN,
            gw_ids=["TXN-1"],
            bank_ids=["BANK-1"],
            confidence=0.5,
        )
        gt = _make_dummy_gt(
            scenario="AMBIGUOUS",
            gw_ids=["TXN-1"],
            bank_ids=["BANK-1"],
            relationship="UNKNOWN",
            root_cause="INSUFFICIENT_EVIDENCE",
            is_exception=True,
        )
        evaluator = BenchmarkEvaluator([er], [gt])
        evals = evaluator.evaluate_all()
        assert evals[0].outcome == EvaluationOutcome.CORRECT_REVIEW


# ===========================================================================
# 4. SCENARIO METRICS
# ===========================================================================

class TestScenarioMetrics:

    def test_scenario_metrics_computed(self):
        results, gt, _ = _run_engine(100)
        evaluator = BenchmarkEvaluator(results, gt)
        evals = evaluator.evaluate_all()
        scenario_data = compute_scenario_metrics(evals)

        # All 13 scenarios plus UNKNOWN should be present
        assert "EXACT_MATCH" in scenario_data
        assert "MDR_GST" in scenario_data
        assert "BATCH_SETTLEMENT" in scenario_data
        assert "AMBIGUOUS" in scenario_data
        assert "UNKNOWN" in scenario_data

        # EXACT_MATCH should have cases
        em = scenario_data["EXACT_MATCH"]
        assert em["total_cases"] > 0


# ===========================================================================
# 5. STRUCTURAL INTEGRITY
# ===========================================================================

class TestStructuralIntegrity:

    def test_no_duplicate_case_ids_in_ground_truth(self):
        gen = SyntheticDataGenerator(seed=42)
        _, _, _, _, gt = gen.generate_dataset(100)
        case_ids = [c.case_id for c in gt]
        assert len(case_ids) == len(set(case_ids)), "Duplicate case IDs in ground truth"

    def test_no_duplicate_reconciliation_ids(self):
        results, _, _ = _run_engine(100)
        rec_ids = [r.reconciliation_id for r in results]
        assert len(rec_ids) == len(set(rec_ids)), "Duplicate reconciliation IDs"

    def test_ground_truth_scenarios_are_valid(self):
        from backend.app.data_generation.scenarios import ScenarioType
        gen = SyntheticDataGenerator(seed=42)
        _, _, _, _, gt = gen.generate_dataset(100)
        valid_scenarios = {s.value for s in ScenarioType}
        for case in gt:
            assert case.scenario in valid_scenarios, f"Unknown scenario: {case.scenario}"


# ===========================================================================
# 6. REPRODUCIBILITY
# ===========================================================================

class TestReproducibility:

    def test_reproducibility(self):
        """Same seed + records must produce identical benchmark results."""
        results_a, gt_a, _ = _run_engine(100, seed=42)
        eval_a = BenchmarkEvaluator(results_a, gt_a)
        evals_a = eval_a.evaluate_all()
        metrics_a = compute_accuracy_metrics(evals_a)

        results_b, gt_b, _ = _run_engine(100, seed=42)
        eval_b = BenchmarkEvaluator(results_b, gt_b)
        evals_b = eval_b.evaluate_all()
        metrics_b = compute_accuracy_metrics(evals_b)

        assert metrics_a == metrics_b


# ===========================================================================
# 7. EDGE CASES
# ===========================================================================

class TestEdgeCases:

    def test_zero_correct_matches(self):
        """All false negatives: engine produces nothing."""
        gt = [_make_dummy_gt(case_id=f"C-{i}", gw_ids=[f"TXN-{i}"]) for i in range(5)]
        evaluator = BenchmarkEvaluator([], gt)
        evals = evaluator.evaluate_all()
        metrics = compute_accuracy_metrics(evals)
        assert metrics["correct_count"] == 0
        assert metrics["false_negative_count"] == 5
        assert metrics["precision"] == 0.0
        assert metrics["recall"] == 0.0

    def test_all_correct(self):
        """Every case perfectly matched."""
        ers = [_make_dummy_result(rec_id=f"R-{i}", gw_ids=[f"TXN-{i}"], bank_ids=[f"BANK-{i}"])
               for i in range(5)]
        gts = [_make_dummy_gt(case_id=f"C-{i}", gw_ids=[f"TXN-{i}"], bank_ids=[f"BANK-{i}"])
               for i in range(5)]
        evaluator = BenchmarkEvaluator(ers, gts)
        evals = evaluator.evaluate_all()
        metrics = compute_accuracy_metrics(evals)
        assert metrics["correct_count"] == 5
        assert metrics["precision"] == 100.0

    def test_all_review(self):
        """All cases sent to review."""
        ers = [_make_dummy_result(
            rec_id=f"R-{i}", gw_ids=[f"TXN-{i}"], bank_ids=[f"BANK-{i}"],
            status=ReconciliationStatus.REVIEW,
        ) for i in range(3)]
        gts = [_make_dummy_gt(case_id=f"C-{i}", gw_ids=[f"TXN-{i}"], bank_ids=[f"BANK-{i}"])
               for i in range(3)]
        evaluator = BenchmarkEvaluator(ers, gts)
        evals = evaluator.evaluate_all()
        review = compute_review_quality(evals)
        assert review["review_count"] == 3
        assert review["correct_review_count"] == 3

    def test_all_unresolved(self):
        """All cases unresolved by engine for non-exception GT cases."""
        ers = [_make_dummy_result(
            rec_id=f"R-{i}", gw_ids=[f"TXN-{i}"], bank_ids=[f"BANK-{i}"],
            status=ReconciliationStatus.UNRESOLVED,
        ) for i in range(3)]
        gts = [_make_dummy_gt(case_id=f"C-{i}", gw_ids=[f"TXN-{i}"], bank_ids=[f"BANK-{i}"])
               for i in range(3)]
        evaluator = BenchmarkEvaluator(ers, gts)
        evals = evaluator.evaluate_all()
        assert all(e.outcome == EvaluationOutcome.FALSE_NEGATIVE for e in evals)

    def test_empty_evaluations(self):
        metrics = compute_accuracy_metrics([])
        assert metrics["total_cases"] == 0
        assert metrics["precision"] == 0.0

    def test_missing_ground_truth_case_handled(self):
        """Engine result with no matching GT case doesn't crash the evaluator."""
        er = _make_dummy_result(gw_ids=["TXN-ORPHAN"])
        gt = _make_dummy_gt(case_id="C1", gw_ids=["TXN-DIFFERENT"])
        evaluator = BenchmarkEvaluator([er], [gt])
        evals = evaluator.evaluate_all()
        # GT case TXN-DIFFERENT has no engine match → false negative
        assert evals[0].outcome == EvaluationOutcome.FALSE_NEGATIVE


# ===========================================================================
# 8. BENCHMARK OUTPUT SCHEMA
# ===========================================================================

class TestBenchmarkOutputSchema:

    def test_benchmark_report_schema(self):
        results, gt, dc = _run_engine(20)
        evaluator = BenchmarkEvaluator(results, gt)
        evals = evaluator.evaluate_all()
        report = build_report(evals, dc, 10.0, 5.0, 20, 42)

        assert isinstance(report, BenchmarkReport)
        # Required top-level keys
        d = report.model_dump()
        assert "benchmark_metadata" in d
        assert "dataset" in d
        assert "decisions" in d
        assert "accuracy" in d
        assert "financial" in d
        assert "performance" in d
        assert "scenarios" in d
        assert "match_types" in d
        assert "failures" in d
        assert "case_evaluations" in d

        # Accuracy sub-keys
        acc = d["accuracy"]
        for key in ["precision", "recall", "f1_score", "match_rate",
                     "correct_count", "incorrect_count", "false_positive_count", "false_negative_count"]:
            assert key in acc, f"Missing accuracy key: {key}"

    def test_json_serializable(self):
        results, gt, dc = _run_engine(20)
        evaluator = BenchmarkEvaluator(results, gt)
        evals = evaluator.evaluate_all()
        report = build_report(evals, dc, 10.0, 5.0, 20, 42)
        # Must not raise
        json_str = json.dumps(report.model_dump(), default=str)
        assert len(json_str) > 0


# ===========================================================================
# 9. INTEGRATION BENCHMARKS
# ===========================================================================

class TestIntegrationBenchmarks:

    def test_100_record_benchmark(self):
        results, gt, dc = _run_engine(100, seed=42)
        evaluator = BenchmarkEvaluator(results, gt)
        evals = evaluator.evaluate_all()
        metrics = compute_accuracy_metrics(evals)
        fin = compute_financial_metrics(evals)

        assert metrics["total_cases"] == len(gt)
        assert metrics["precision"] >= 0
        assert metrics["recall"] >= 0
        assert fin["total_expected_value"] > 0

    def test_500_record_benchmark(self):
        results, gt, dc = _run_engine(500, seed=42)
        evaluator = BenchmarkEvaluator(results, gt)
        evals = evaluator.evaluate_all()
        metrics = compute_accuracy_metrics(evals)
        fin = compute_financial_metrics(evals)

        assert metrics["total_cases"] == len(gt)
        assert fin["total_expected_value"] > 0

    def test_1000_record_benchmark(self):
        start = time.time()
        results, gt, dc = _run_engine(1000, seed=42)
        evaluator = BenchmarkEvaluator(results, gt)
        evals = evaluator.evaluate_all()
        elapsed = (time.time() - start) * 1000
        metrics = compute_accuracy_metrics(evals)

        assert metrics["total_cases"] == len(gt)
        assert elapsed < 30000, f"1000-record benchmark took {elapsed:.0f}ms (>30s)"
