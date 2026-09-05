#!/usr/bin/env python3
"""CLI runner for Recon-AI Reconciliation Engine."""

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


def main():
    parser = argparse.ArgumentParser(description="Run the Recon-AI Deterministic Reconciliation Engine")
    parser.add_argument("--records", type=int, default=100, help="Number of records to generate and reconcile")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Random seed")
    args = parser.parse_args()

    print(f"Generating synthetic financial dataset with {args.records} cases (seed={args.seed})...")
    generator = SyntheticDataGenerator(seed=args.seed)
    erp_orders, gateway_txns, settlements, bank_txns, _ = generator.generate_dataset(total_cases=args.records)

    print("Running Autonomous Deterministic Reconciliation Engine...")
    engine = ReconciliationEngine()
    
    start_time = time.time()
    result = engine.reconcile(erp_orders, gateway_txns, settlements, bank_txns)
    total_ms = (time.time() - start_time) * 1000.0

    summary = result["summary"]

    print("\n=============================================")
    print("       RECON-AI RECONCILIATION RUN")
    print("=============================================")
    print(f"ERP records:                 {len(erp_orders)}")
    print(f"Gateway transactions:        {len(gateway_txns)}")
    print(f"Gateway settlements:         {len(settlements)}")
    print(f"Bank transactions:           {len(bank_txns)}")
    print()
    print(f"Resolved:                    {summary['resolved_count']}")
    print(f"Human Review:                {summary['review_count']}")
    print(f"Unresolved:                  {summary['unresolved_count']}")
    print()
    print(f"Exact matches:               {summary['exact_match_count']}")
    print(f"Batch matches:               {summary['batch_match_count']}")
    print(f"Fee reconciliations:         {summary['fee_reconciled_count']}")
    print(f"Missing bank:                {summary['missing_bank_count']}")
    print(f"Missing ERP:                 {summary['missing_erp_count']}")
    print(f"Duplicates:                  {summary['duplicate_count']}")
    print()
    print(f"Expected financial value:    ₹{summary['total_expected_value']:,.2f}")
    print(f"Actual bank value:           ₹{summary['total_actual_value']:,.2f}")
    print(f"Unresolved exposure:         ₹{summary['total_unresolved_value']:,.2f}")
    print()
    print(f"Processing time:             {total_ms:.2f} ms")
    print("=============================================\n")


if __name__ == "__main__":
    main()
