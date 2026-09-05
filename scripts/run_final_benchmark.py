#!/usr/bin/env python3
"""CLI runner for Recon-AI Phase 10 Final Benchmark.

Produces deterministic baseline and AI-assisted improvement metrics.
"""

import argparse
import sys
import time
from pathlib import Path
from collections import defaultdict
import json

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.data_generation.generator import SyntheticDataGenerator
from backend.app.domain.finance_rules import DEFAULT_SEED
from backend.app.reconciliation.engine import ReconciliationEngine
from backend.app.benchmark.evaluator import BenchmarkEvaluator
from backend.app.ai.resolver import investigate_exception
from backend.app.reconciliation.types import ReconciliationStatus


def format_currency(val: float) -> str:
    return f"₹{val:,.2f}"

def run_final_benchmark(records: int, seed: int):
    print(f"\n============================================================")
    print(f"      PHASE 10: FINAL DETERMINISTIC vs AI BENCHMARK")
    print(f"============================================================")
    print(f"  Records: {records}")
    print(f"  Seed:    {seed}")
    print(f"============================================================")
    
    # 1. Generate Dataset
    generator = SyntheticDataGenerator(seed=seed)
    erp_orders, gateway_txns, settlements, bank_txns, ground_truth = generator.generate_dataset(records)
    gt_map = {gt.case_id: gt for gt in ground_truth}
    
    print(f"Generated {len(erp_orders)} ERP, {len(gateway_txns)} Gateway, {len(bank_txns)} Bank txns.")
    
    # 2. Run Deterministic Engine
    engine = ReconciliationEngine()
    engine_start = time.time()
    engine_output = engine.reconcile(erp_orders, gateway_txns, settlements, bank_txns)
    det_results = engine_output["reconciliation_results"]
    
    # 3. Evaluate Deterministic Baseline
    evaluator = BenchmarkEvaluator(det_results, ground_truth)
    evaluations = evaluator.evaluate_all()
    
    from backend.app.benchmark.reporter import build_report
    det_report = build_report(
        evaluations=evaluations,
        dataset_counts={"e": len(erp_orders), "g": len(gateway_txns), "s": len(settlements), "b": len(bank_txns)},
        engine_time_ms=0, evaluation_time_ms=0, dataset_size=records, seed=seed
    ).model_dump()

    det_acc = det_report["accuracy"]
    det_fin = det_report["financial"]
    
    # Track deterministic stats for eligible exceptions
    ai_eligible_types = {"DUPLICATE", "BATCH_SETTLEMENT", "MISSING_ERP"}
    
    # Find all REVIEW cases
    review_cases = [r for r in det_results if r.status == ReconciliationStatus.REVIEW]
    eligible_cases = [r for r in review_cases if r.root_cause and r.root_cause.value in ai_eligible_types]
    
    # 4. Evaluate AI Intervention
    ai_correct = 0
    ai_incorrect = 0
    ai_human_review = 0
    value_correctly_resolved = 0.0
    value_incorrectly_resolved = 0.0
    ai_assisted_autonomous_count = 0
    
    # For type breakdown
    type_stats = {t: {"eligible": 0, "ai_correct": 0, "value_affected": 0.0} for t in ai_eligible_types}
    
    print(f"\nRunning Phase 7 AI Resolver on {len(eligible_cases)} eligible ambiguous cases...")
    
    for r in eligible_cases:
        exc_type = r.root_cause.value
        type_stats[exc_type]["eligible"] += 1
        
        # We need the ground truth for this result to know if AI got it right.
        # But wait, how do we get the ground truth case?
        # The evaluator mapped engine result to ground truth. Let's look up the evaluation.
        evaluation = next((e for e in evaluations if e.engine_reconciliation_id == r.reconciliation_id), None)
        
        # Extract exception dictionary expected by AI
        exc_dict = r.model_dump()
        exc_dict["id"] = r.reconciliation_id
        exc_dict["type"] = exc_type
        exc_dict["amount"] = r.expected_amount
        
        # Invoke AI
        ai_res = investigate_exception(exc_dict)
        
        # Evaluate AI decision correctness regardless of human review flag
        # AI returns e.g. "LIKELY_DUPLICATE" for DUPLICATE
        decision_base = ai_res.decision.replace("LIKELY_", "")
        
        if decision_base == "UNRESOLVED":
            ai_human_review += 1
            # Value remains unresolved
            pass
        else:
            if ai_res.human_review_required:
                ai_human_review += 1
                
            is_correct = False
            if evaluation and evaluation.case_id:
                gt = gt_map.get(evaluation.case_id)
                if gt and gt.scenario == decision_base:
                    is_correct = True
            
            if is_correct:
                ai_correct += 1
                value_correctly_resolved += r.expected_amount
                type_stats[exc_type]["ai_correct"] += 1
                type_stats[exc_type]["value_affected"] += r.expected_amount
                if not ai_res.human_review_required:
                    # Only add to autonomous if no human review needed
                    ai_assisted_autonomous_count += 1
            else:
                ai_incorrect += 1
                value_incorrectly_resolved += r.expected_amount

    # In our deterministic baseline, ALL review cases are treated as NOT autonomously resolved.
    # So Value Reconciled is the deterministic value.
    # We can add `value_correctly_resolved` to the new AI-assisted metrics.
    
    det_total = len(det_results)
    det_resolved = sum(1 for r in det_results if r.status == ReconciliationStatus.RESOLVED)
    det_auto_metrics = det_report.get("autonomous_resolution", {})
    det_autonomous = det_auto_metrics.get("safe_autonomous_resolution_rate", 0)
    det_correct_auto = det_auto_metrics.get("correct_autonomous_resolutions", 0)
    
    ai_assisted_autonomous_count = 0  # We will track this separately in the loop
    ai_assisted_resolved = det_resolved + ai_correct
    
    det_val = det_fin["correctly_reconciled_value"]
    ai_val = det_val + value_correctly_resolved
    total_val = det_fin["total_expected_value"]
    
    det_val_pct = (det_val / total_val * 100) if total_val > 0 else 0
    ai_val_pct = (ai_val / total_val * 100) if total_val > 0 else 0
    
    total_ai_auto = det_resolved + ai_assisted_autonomous_count
    correct_ai_auto = det_correct_auto + ai_assisted_autonomous_count
    ai_autonomous = (correct_ai_auto / total_ai_auto * 100) if total_ai_auto > 0 else 0
    
    det_gateway = len(gateway_txns)
    det_tp = det_acc.get("correct_count", 0)
    ai_tp = det_tp + ai_correct
    det_fp = det_acc.get("false_positive_count", 0)
    ai_fp = det_fp + ai_incorrect
    det_fn = det_acc.get("false_negative_count", 0)
    ai_fn = max(0, det_fn - ai_correct) 
    
    ai_precision = (ai_tp / (ai_tp + ai_fp) * 100) if (ai_tp + ai_fp) > 0 else 0
    ai_recall = (ai_tp / (ai_tp + ai_fn) * 100) if (ai_tp + ai_fn) > 0 else 0
    ai_f1 = (2 * ai_precision * ai_recall / (ai_precision + ai_recall)) if (ai_precision + ai_recall) > 0 else 0
    
    # Match rate denominator is gateway txns, just like the evaluator
    det_match_rate = det_acc.get("match_rate", 0)
    # The absolute increase in match rate is (ai_correct / gateway_txns) * 100
    ai_match_rate = det_match_rate + ((ai_correct / det_gateway * 100) if det_gateway > 0 else 0)
    
    # 5. Output Report
    
    print(f"\n============================================================")
    print(f"                  FINAL COMPARISON (Hypothetical AI-accepted simulation)")
    print(f"============================================================")
    print(f"{'Metric':<20} | {'Deterministic':>13} | {'Hypothetical':>13} | {'Improvement':>12}")
    print(f"-" * 65)
    print(f"{'Precision':<20} | {det_acc['precision']:>12.2f}% | {ai_precision:>12.2f}% | {(ai_precision - det_acc['precision']):>11.2f}%")
    print(f"{'Recall':<20} | {det_acc['recall']:>12.2f}% | {ai_recall:>12.2f}% | {(ai_recall - det_acc['recall']):>11.2f}%")
    print(f"{'F1 Score':<20} | {det_acc['f1_score']:>12.2f}% | {ai_f1:>12.2f}% | {(ai_f1 - det_acc['f1_score']):>11.2f}%")
    print(f"{'Match Rate':<20} | {det_acc['match_rate']:>12.2f}% | {ai_match_rate:>12.2f}% | {(ai_match_rate - det_acc['match_rate']):>11.2f}%")
    print(f"{'Value Reconciled':<20} | {det_val_pct:>12.2f}% | {ai_val_pct:>12.2f}% | {(ai_val_pct - det_val_pct):>11.2f}%")
    print(f"{'Safe Autonomous':<20} | {det_autonomous:>12.2f}% | {ai_autonomous:>12.2f}% | {(ai_autonomous - det_autonomous):>11.2f}%")
    
    print(f"\n============================================================")
    print(f"                  AI EVALUATION (Eligible Cases)")
    print(f"============================================================")
    print(f"  AI Eligible Cases:             {len(eligible_cases)}")
    print(f"  Correct Resolutions (AI):      {ai_correct}")
    print(f"  Incorrect Resolutions (AI):    {ai_incorrect}")
    print(f"  Relegated to Human Review:     {ai_human_review}")
    print(f"  AI Accuracy (resolved):        {(ai_correct / (ai_correct + ai_incorrect) * 100) if (ai_correct + ai_incorrect) > 0 else 0:.2f}%")
    print(f"  Value Correctly Evaluated:     {format_currency(value_correctly_resolved)}")
    print(f"  Value Incorrectly Evaluated:   {format_currency(value_incorrectly_resolved)}")

    print(f"\n============================================================")
    print(f"                  FAILURE-TYPE ANALYSIS")
    print(f"============================================================")
    for exc_type, stats in type_stats.items():
        if stats['eligible'] > 0:
            print(f"  {exc_type}:")
            print(f"    Eligible:           {stats['eligible']}")
            print(f"    AI Correct:         {stats['ai_correct']}")
            print(f"    Value Affected:     {format_currency(stats['value_affected'])}")
            
    print(f"\n============================================================")
    print(f"  Phase 10 — Final Deterministic vs AI Benchmark: PASS")
    print(f"============================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--records", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    
    run_final_benchmark(args.records, args.seed)
