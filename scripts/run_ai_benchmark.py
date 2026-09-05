#!/usr/bin/env python3
"""CLI runner for ReconPulse AI Phase 7 AI Ambiguity Resolver Benchmark.

This script evaluates how well the AI resolver handles ambiguous exceptions 
that were correctly flagged by the deterministic engine.
"""

import argparse
import sys
import time
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.data_generation.generator import SyntheticDataGenerator
from backend.app.domain.finance_rules import DEFAULT_SEED
from backend.app.reconciliation.engine import ReconciliationEngine
from backend.app.reconciliation.types import ReconciliationStatus
from backend.app.ai.resolver import investigate_exception


def run_ai_benchmark(records: int, seed: int):
    print(f"\n============================================================")
    print(f"       RECON-AI PHASE 7 AI RESOLVER BENCHMARK")
    print(f"============================================================\n")

    # 1. Generate dataset
    generator = SyntheticDataGenerator(seed=seed)
    erp_orders, gateway_txns, settlements, bank_txns, ground_truth = generator.generate_dataset(records)

    print(f"Dataset Generated ({records} cases, seed {seed})")

    # 2. Run deterministic engine
    engine = ReconciliationEngine()
    engine_output = engine.reconcile(erp_orders, gateway_txns, settlements, bank_txns)
    engine_results = engine_output["reconciliation_results"]

    # 3. Identify ambiguous exceptions
    # We define AI-eligible exceptions as those marked REVIEW or UNRESOLVED by the deterministic engine
    # and falling into our targeted ambiguity classes.
    eligible_types = {"DUPLICATE", "BATCH_SETTLEMENT", "MISSING_ERP"}
    
    # Map ground truth by gateway ID for easy lookup
    gt_by_gw_id = {}
    for gt in ground_truth:
        for gid in gt.gateway_transaction_ids:
            gt_by_gw_id[gid] = gt

    metrics = {
        "ai_eligible_cases": 0,
        "ai_resolved_cases": 0,
        "ai_correctly_resolved": 0,
        "ai_incorrectly_resolved": 0,
        "ai_unresolved": 0,
        "value_correctly_resolved": 0.0,
        "value_incorrectly_resolved": 0.0,
        "human_review_cases": 0,
    }

    start_time = time.time()

    for res in engine_results:
        # Check eligibility
        if res.status not in (ReconciliationStatus.REVIEW, ReconciliationStatus.UNRESOLVED):
            continue
        
        exc_type = res.root_cause.value if res.root_cause else "UNKNOWN"
        if exc_type not in eligible_types:
            continue
            
        metrics["ai_eligible_cases"] += 1
        
        # We need the ground truth for this result
        gt_case = None
        for gid in res.gateway_transaction_ids:
            if gid in gt_by_gw_id:
                gt_case = gt_by_gw_id[gid]
                break
                
        if not gt_case:
            # Should not happen in controlled synthetic tests but safe fallback
            continue

        # Prepare payload for AI (mimic Phase 4 schema shape)
        exception_dict = {
            "id": res.reconciliation_id,
            "type": exc_type,
            "status": res.status.value,
            "amount": res.expected_amount,
            "difference": res.difference,
            "evidence": {
                "matched_by": [m.value for m in res.match_type.value] if isinstance(res.match_type.value, list) else [res.match_type.value],
            }
        }

        # 4. Invoke AI Resolver
        ai_recommendation = investigate_exception(exception_dict)

        if ai_recommendation.human_review_required:
            metrics["human_review_cases"] += 1

        if ai_recommendation.decision == "UNRESOLVED":
            metrics["ai_unresolved"] += 1
        else:
            metrics["ai_resolved_cases"] += 1
            
            # Check correctness against ground truth
            # Maps AI decision to expected ground truth scenarios/root causes
            is_correct = False
            
            if ai_recommendation.decision == "LIKELY_DUPLICATE" and (gt_case.scenario == "DUPLICATE" or gt_case.root_cause == "DUPLICATE"):
                is_correct = True
            elif ai_recommendation.decision == "LIKELY_BATCH_SETTLEMENT" and gt_case.scenario == "BATCH_SETTLEMENT":
                is_correct = True
            elif ai_recommendation.decision == "LIKELY_MISSING_ERP" and (gt_case.root_cause == "MISSING_ERP" or gt_case.scenario == "MISSING_ERP"):
                is_correct = True

            if is_correct:
                metrics["ai_correctly_resolved"] += 1
                metrics["value_correctly_resolved"] += abs(res.expected_amount)
            else:
                metrics["ai_incorrectly_resolved"] += 1
                metrics["value_incorrectly_resolved"] += abs(res.expected_amount)

    eval_time = time.time() - start_time

    # Calculate Rates
    ai_resolution_rate = 0.0
    ai_resolution_accuracy = 0.0
    human_review_rate = 0.0

    if metrics["ai_eligible_cases"] > 0:
        ai_resolution_rate = (metrics["ai_resolved_cases"] / metrics["ai_eligible_cases"]) * 100
        human_review_rate = (metrics["human_review_cases"] / metrics["ai_eligible_cases"]) * 100
        
    if metrics["ai_resolved_cases"] > 0:
        ai_resolution_accuracy = (metrics["ai_correctly_resolved"] / metrics["ai_resolved_cases"]) * 100

    print("AI Evaluation Results")
    print("------------------------------------------------------------")
    print(f"  AI Eligible Cases:             {metrics['ai_eligible_cases']}")
    print(f"  AI Resolved Cases:             {metrics['ai_resolved_cases']}")
    print(f"  AI Correctly Resolved:         {metrics['ai_correctly_resolved']}")
    print(f"  AI Incorrectly Resolved:       {metrics['ai_incorrectly_resolved']}")
    print(f"  AI Unresolved:                 {metrics['ai_unresolved']}")
    print(f"  Human-Review Cases:            {metrics['human_review_cases']}")
    print("")
    print(f"  AI Resolution Rate:            {ai_resolution_rate:.2f}%")
    print(f"  AI Resolution Accuracy:        {ai_resolution_accuracy:.2f}%")
    print(f"  Human-Review Rate:             {human_review_rate:.2f}%")
    print("")
    print(f"  Value Correctly Resolved:      ₹{metrics['value_correctly_resolved']:,.2f}")
    print(f"  Value Incorrectly Resolved:    ₹{metrics['value_incorrectly_resolved']:,.2f}")
    print("------------------------------------------------------------")
    print(f"Evaluation Time: {eval_time*1000:.2f} ms\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the AI Resolver Benchmark")
    parser.add_argument("--records", type=int, default=100, help="Number of cases to generate")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    args = parser.parse_args()
    run_ai_benchmark(args.records, args.seed)
