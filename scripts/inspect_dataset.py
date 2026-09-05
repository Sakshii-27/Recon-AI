#!/usr/bin/env python3
"""CLI utility to inspect representative scenario cases from the generated dataset."""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def inspect_dataset(data_dir: Path, scenario_filter: str = None, case_limit: int = 2):
    synthetic_dir = data_dir / "synthetic"
    ground_truth_file = data_dir / "ground_truth" / "ground_truth.json"

    if not ground_truth_file.exists():
        print(f"Error: ground_truth.json not found in {ground_truth_file}")
        sys.exit(1)

    with open(ground_truth_file, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)
    with open(synthetic_dir / "erp_orders.json", "r", encoding="utf-8") as f:
        erp_orders = {e["order_id"]: e for e in json.load(f)}
    with open(synthetic_dir / "gateway_transactions.json", "r", encoding="utf-8") as f:
        gateway_txns = {g["gateway_transaction_id"]: g for g in json.load(f)}
    with open(synthetic_dir / "bank_transactions.json", "r", encoding="utf-8") as f:
        bank_txns = {b["bank_transaction_id"]: b for b in json.load(f)}

    matching_cases = [
        c for c in ground_truth
        if scenario_filter is None or c["scenario"].upper() == scenario_filter.upper()
    ]

    if not matching_cases:
        print(f"No cases found matching scenario: {scenario_filter}")
        available = sorted(set(c["scenario"] for c in ground_truth))
        print(f"Available scenarios: {', '.join(available)}")
        return

    print(f"\nDisplaying {min(len(matching_cases), case_limit)} sample case(s) for scenario: {scenario_filter or 'ALL'}\n")
    print("=" * 65)

    for case in matching_cases[:case_limit]:
        print(f"Case ID:        {case['case_id']}")
        print(f"Scenario:       {case['scenario']}")
        print(f"Relationship:   {case['expected_relationship']}")
        print(f"Description:    {case['description']}")
        print(f"Is Exception:   {case['is_exception']}")
        if case.get("root_cause"):
            print(f"Root Cause:     {case['root_cause']}")

        print("\n  [ ERP Orders ]")
        if not case["erp_order_ids"]:
            print("    (None - missing ERP record)")
        for eid in case["erp_order_ids"]:
            e = erp_orders.get(eid)
            if e:
                print(f"    - {e['order_id']} | Ref: {e['order_reference']} | ₹{e['gross_amount']:,.2f} | {e['order_date']}")

        print("\n  [ Gateway Transactions ]")
        if not case["gateway_transaction_ids"]:
            print("    (None)")
        for gid in case["gateway_transaction_ids"]:
            g = gateway_txns.get(gid)
            if g:
                print(f"    - {g['gateway_transaction_id']} | Cap: ₹{g['captured_amount']:,.2f} | Fee: ₹{g['gateway_fee']:,.2f} + GST ₹{g['gst_on_fee']:,.2f} | Settle: {g['settlement_id']}")

        print(f"\n  Expected Net Payout: ₹{case['expected_net_amount']:,.2f}")

        print("\n  [ Bank Statement Deposits ]")
        if not case["bank_transaction_ids"]:
            print("    (None - missing bank credit!)")
        for bid in case["bank_transaction_ids"]:
            b = bank_txns.get(bid)
            if b:
                print(f"    - {b['bank_transaction_id']} | Date: {b['transaction_date']} | Credit: ₹{b['credit_amount']:,.2f} | Descr: {b['description']}")

        print("-" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect scenario cases in Recon-AI synthetic dataset")
    parser.add_argument("--scenario", type=str, default=None, help="Scenario to inspect (e.g. BATCH_SETTLEMENT, MISSING_BANK)")
    parser.add_argument("--limit", type=int, default=1, help="Max cases to show (default: 1)")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory path")
    args = parser.parse_args()

    inspect_dataset(Path(args.data_dir), scenario_filter=args.scenario, case_limit=args.limit)
