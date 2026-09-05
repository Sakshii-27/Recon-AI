#!/usr/bin/env python3
"""CLI runner for Recon-AI Benchmark & Evaluation Suite.

Usage:
    python scripts/run_benchmark.py --records 100 --seed 42
    python scripts/run_benchmark.py --records 500 --seed 42
    python scripts/run_benchmark.py --records 1000 --seed 42
    python scripts/run_benchmark.py --records 500 --seeds 42,43,44,45,46
"""

import argparse
import statistics
import sys
import time
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.data_generation.generator import SyntheticDataGenerator
from backend.app.domain.finance_rules import DEFAULT_SEED
from backend.app.reconciliation.engine import ReconciliationEngine
from backend.app.benchmark.evaluator import BenchmarkEvaluator
from backend.app.benchmark.reporter import build_report, save_report_json, print_terminal_report


def run_single_benchmark(records: int, seed: int, save_json: bool = True) -> dict:
    """Runs a single benchmark: generate → reconcile → evaluate → report."""

    # 1. Generate dataset (includes ground truth, but engine won't see it)
    generator = SyntheticDataGenerator(seed=seed)
    erp_orders, gateway_txns, settlements, bank_txns, ground_truth = generator.generate_dataset(records)

    dataset_counts = {
        "erp_records": len(erp_orders),
        "gateway_transactions": len(gateway_txns),
        "gateway_settlements": len(settlements),
        "bank_transactions": len(bank_txns),
    }

    # 2. Run the Phase 2 engine (NO ground truth passed)
    engine = ReconciliationEngine()
    engine_start = time.time()
    engine_output = engine.reconcile(erp_orders, gateway_txns, settlements, bank_txns)
    engine_time_ms = (time.time() - engine_start) * 1000.0

    engine_results = engine_output["reconciliation_results"]

    # 3. Evaluate against ground truth (AFTER engine has completed)
    eval_start = time.time()
    evaluator = BenchmarkEvaluator(engine_results, ground_truth)
    evaluations = evaluator.evaluate_all()
    eval_time_ms = (time.time() - eval_start) * 1000.0

    # 4. Build report
    report = build_report(
        evaluations=evaluations,
        dataset_counts=dataset_counts,
        engine_time_ms=engine_time_ms,
        evaluation_time_ms=eval_time_ms,
        dataset_size=records,
        seed=seed,
    )

    # 5. Print terminal report
    print_terminal_report(report)

    # 6. Save JSON report
    if save_json:
        output_path = Path("data/benchmark") / f"benchmark_{records}_seed{seed}.json"
        save_report_json(report, output_path)
        print(f"  JSON report saved to: {output_path}")

    return report.model_dump()


def run_multi_seed_benchmark(records: int, seeds: list) -> None:
    """Runs benchmarks across multiple seeds and reports aggregate statistics."""
    all_precisions = []
    all_recalls = []
    all_f1s = []
    all_match_rates = []
    all_value_pcts = []

    for seed in seeds:
        print(f"\n{'='*60}")
        print(f"  Seed: {seed}")
        print(f"{'='*60}")
        report_data = run_single_benchmark(records, seed, save_json=True)
        acc = report_data.get("accuracy", {})
        fin = report_data.get("financial", {})
        all_precisions.append(acc.get("precision", 0))
        all_recalls.append(acc.get("recall", 0))
        all_f1s.append(acc.get("f1_score", 0))
        all_match_rates.append(acc.get("match_rate", 0))
        all_value_pcts.append(fin.get("value_reconciliation_percentage", 0))

    print(f"\n{'='*60}")
    print(f"  MULTI-SEED AGGREGATE ({len(seeds)} seeds, {records} records each)")
    print(f"{'='*60}")

    def _stats(values):
        if len(values) < 2:
            return {"mean": values[0] if values else 0, "min": values[0] if values else 0,
                    "max": values[0] if values else 0, "stdev": 0}
        return {
            "mean": round(statistics.mean(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "stdev": round(statistics.stdev(values), 2),
        }

    for label, values in [
        ("Precision", all_precisions),
        ("Recall", all_recalls),
        ("F1 Score", all_f1s),
        ("Match Rate", all_match_rates),
        ("Value Reconciliation %", all_value_pcts),
    ]:
        s = _stats(values)
        print(f"  {label:<25} mean={s['mean']:.2f}%  min={s['min']:.2f}%  max={s['max']:.2f}%  stdev={s['stdev']:.2f}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Run the Recon-AI Benchmark & Evaluation Suite")
    parser.add_argument("--records", type=int, default=100, help="Number of cases to generate and evaluate")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed (single run)")
    parser.add_argument("--seeds", type=str, default=None, help="Comma-separated seeds for multi-seed evaluation")
    args = parser.parse_args()

    if args.seeds:
        seed_list = [int(s.strip()) for s in args.seeds.split(",")]
        run_multi_seed_benchmark(args.records, seed_list)
    else:
        run_single_benchmark(args.records, args.seed)


if __name__ == "__main__":
    main()
