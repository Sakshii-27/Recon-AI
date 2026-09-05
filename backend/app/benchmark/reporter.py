"""Benchmark report assembler: combines all metrics into terminal + JSON output."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from backend.app.benchmark.types import (
    BenchmarkReport,
    CaseEvaluation,
    EvaluationOutcome,
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


def build_report(
    evaluations: List[CaseEvaluation],
    dataset_counts: Dict[str, int],
    engine_time_ms: float,
    evaluation_time_ms: float,
    dataset_size: int,
    seed: int,
) -> BenchmarkReport:
    """Builds the complete benchmark report from case evaluations."""
    total_benchmark_ms = engine_time_ms + evaluation_time_ms

    accuracy = compute_accuracy_metrics(evaluations)
    financial = compute_financial_metrics(evaluations)
    decisions = compute_decision_metrics(evaluations)
    scenarios = compute_scenario_metrics(evaluations)
    match_types = compute_match_type_metrics(evaluations)
    review = compute_review_quality(evaluations)
    autonomous = compute_autonomous_resolution(evaluations)

    records_processed = dataset_counts.get("gateway_transactions", 0)
    throughput = 0.0
    if engine_time_ms > 0:
        throughput = float(records_processed / (engine_time_ms / 1000.0))

    performance = {
        "engine_time_ms": round(engine_time_ms, 2),
        "evaluation_time_ms": round(evaluation_time_ms, 2),
        "total_benchmark_time_ms": round(total_benchmark_ms, 2),
        "throughput_records_per_second": round(throughput, 1),
        "throughput_cases_per_second": round(
            dataset_size / (engine_time_ms / 1000.0), 1
        ) if engine_time_ms > 0 else 0.0,
    }

    # Build failure list
    failures = []
    fp_details = []
    fn_details = []

    for e in evaluations:
        if e.outcome in (
            EvaluationOutcome.FALSE_POSITIVE,
            EvaluationOutcome.FALSE_NEGATIVE,
            EvaluationOutcome.INCORRECT_MATCH,
        ):
            entry = {
                "case_id": e.case_id,
                "scenario": e.scenario,
                "outcome": e.outcome.value,
                "gt_gateway_ids": e.gt_gateway_transaction_ids,
                "gt_bank_ids": e.gt_bank_transaction_ids,
                "engine_gateway_ids": e.engine_gateway_ids,
                "engine_bank_ids": e.engine_bank_ids,
                "engine_status": e.engine_status,
                "engine_match_type": e.engine_match_type,
                "engine_confidence": e.engine_confidence,
                "financial_value": e.financial_value,
                "failure_reason": e.failure_reason.value if e.failure_reason else None,
                "failure_detail": e.failure_detail,
            }
            failures.append(entry)

            if e.outcome == EvaluationOutcome.FALSE_POSITIVE:
                fp_details.append(entry)
            elif e.outcome == EvaluationOutcome.FALSE_NEGATIVE:
                fn_details.append(entry)

    report = BenchmarkReport(
        benchmark_metadata={
            "dataset_size": dataset_size,
            "seed": seed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engine_version": "phase-2",
        },
        dataset=dataset_counts,
        decisions=decisions,
        accuracy=accuracy,
        financial=financial,
        performance=performance,
        scenarios=scenarios,
        match_types=match_types,
        review_quality=review,
        autonomous_resolution=autonomous,
        failures=failures,
        false_positive_details=fp_details,
        false_negative_details=fn_details,
        case_evaluations=[e.model_dump() for e in evaluations],
    )

    return report


def save_report_json(report: BenchmarkReport, filepath: Path) -> None:
    """Saves benchmark report as JSON."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2, default=str)


def print_terminal_report(report: BenchmarkReport) -> None:
    """Prints the human-readable terminal report."""
    d = report.dataset
    dec = report.decisions
    acc = report.accuracy
    fin = report.financial
    perf = report.performance
    rev = report.review_quality
    auto = report.autonomous_resolution
    scenarios = report.scenarios

    print()
    print("=" * 60)
    print("              RECON-AI BENCHMARK REPORT")
    print("=" * 60)

    print()
    print("Dataset")
    print("-" * 60)
    print(f"  Cases:                       {report.benchmark_metadata.get('dataset_size', 'N/A')}")
    print(f"  ERP records:                 {d.get('erp_records', 0)}")
    print(f"  Gateway transactions:        {d.get('gateway_transactions', 0)}")
    print(f"  Gateway settlements:         {d.get('gateway_settlements', 0)}")
    print(f"  Bank transactions:           {d.get('bank_transactions', 0)}")

    print()
    print("Decision Quality")
    print("-" * 60)
    print(f"  Resolved:                    {dec.get('resolved', 0)}")
    print(f"  Human Review:                {dec.get('review', 0)}")
    print(f"  Unresolved:                  {dec.get('unresolved', 0)}")
    print()
    print(f"  Correct:                     {acc.get('correct_count', 0)}")
    print(f"  Incorrect:                   {acc.get('incorrect_count', 0)}")
    print(f"  False Positives:             {acc.get('false_positive_count', 0)}")
    print(f"  False Negatives:             {acc.get('false_negative_count', 0)}")
    print()
    print(f"  Precision:                   {acc.get('precision', 0):.2f}%")
    print(f"  Recall:                      {acc.get('recall', 0):.2f}%")
    print(f"  F1 Score:                    {acc.get('f1_score', 0):.2f}%")
    print(f"  Match Rate:                  {acc.get('match_rate', 0):.2f}%")

    print()
    print("Autonomous Resolution Quality")
    print("-" * 60)
    print(f"  Total autonomous:            {auto.get('total_autonomous_resolutions', 0)}")
    print(f"  Correct autonomous:          {auto.get('correct_autonomous_resolutions', 0)}")
    print(f"  Safe resolution rate:        {auto.get('safe_autonomous_resolution_rate', 0):.2f}%")

    print()
    print("Review Quality")
    print("-" * 60)
    print(f"  Review count:                {rev.get('review_count', 0)}")
    print(f"  Correct reviews:             {rev.get('correct_review_count', 0)}")
    print(f"  Review precision:            {rev.get('review_precision', 0):.2f}%")

    print()
    print("Financial Coverage")
    print("-" * 60)
    print(f"  Expected Value:              ₹{fin.get('total_expected_value', 0):,.2f}")
    print(f"  Actual Bank Value:           ₹{fin.get('total_actual_bank_value', 0):,.2f}")
    print(f"  Value Reconciled:            ₹{fin.get('correctly_reconciled_value', 0):,.2f}")
    print(f"  Value Reconciliation:        {fin.get('value_reconciliation_percentage', 0):.2f}%")
    print(f"  Unreconciled Value:          ₹{fin.get('unreconciled_value', 0):,.2f}")
    print(f"  False Positive Value:        ₹{fin.get('false_positive_financial_value', 0):,.2f}")
    print(f"  False Negative Value:        ₹{fin.get('false_negative_financial_value', 0):,.2f}")

    print()
    print("Performance")
    print("-" * 60)
    print(f"  Engine Time:                 {perf.get('engine_time_ms', 0):.2f} ms")
    print(f"  Evaluation Time:             {perf.get('evaluation_time_ms', 0):.2f} ms")
    print(f"  Throughput:                  {perf.get('throughput_records_per_second', 0):.0f} records/sec")

    print()
    print("Scenario Performance")
    print("-" * 60)
    for scenario_name in [
        "EXACT_MATCH", "MDR_GST", "T_PLUS_1", "T_PLUS_2",
        "BATCH_SETTLEMENT", "REFUND", "CHARGEBACK", "PARTIAL_SETTLEMENT",
        "DUPLICATE", "MISSING_BANK", "MISSING_ERP", "FEE_ANOMALY",
        "AMBIGUOUS",
    ]:
        sd = scenarios.get(scenario_name, {})
        total = sd.get("total_cases", 0)
        mr = sd.get("match_rate", 0)
        if total > 0:
            print(f"  {scenario_name:<25} {mr:6.2f}%  ({sd.get('correct', 0)}/{total})")

    # Failure summary
    if report.failures:
        print()
        print("Failure Summary")
        print("-" * 60)
        for f in report.failures[:10]:  # Show first 10
            print(
                f"  {f['case_id']}  {f['scenario']:<20} "
                f"{f['outcome']:<20} "
                f"₹{f['financial_value']:,.2f}  "
                f"{f.get('failure_reason', 'N/A')}"
            )
        if len(report.failures) > 10:
            print(f"  ... and {len(report.failures) - 10} more failures")

    print()
    print("=" * 60)
    print()
