#!/usr/bin/env python3
"""Dataset validation script for Recon-AI.

Validates domain constraints, financial consistency, bank balance arithmetic,
referential integrity, scenario distribution, and ground-truth isolation.
"""

import argparse
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.domain.finance_rules import (
    DEFAULT_GST_ON_MDR,
    DEFAULT_MDR_RATE,
    DEFAULT_ROUNDING_TOLERANCE,
    calculate_total_fee,
    round_currency,
)
from backend.app.domain.models import (
    BankTransaction,
    ERPOrder,
    GatewaySettlement,
    GatewayTransaction,
    GroundTruthCase,
)


def validate_dataset(data_dir: Path) -> bool:
    synthetic_dir = data_dir / "synthetic"
    ground_truth_dir = data_dir / "ground_truth"

    errors = []

    # 1. Check file existence
    required_files = [
        synthetic_dir / "erp_orders.json",
        synthetic_dir / "erp_orders.csv",
        synthetic_dir / "gateway_transactions.json",
        synthetic_dir / "gateway_transactions.csv",
        synthetic_dir / "gateway_settlements.json",
        synthetic_dir / "gateway_settlements.csv",
        synthetic_dir / "bank_transactions.json",
        synthetic_dir / "bank_transactions.csv",
        ground_truth_dir / "ground_truth.json",
    ]
    for rf in required_files:
        if not rf.exists():
            errors.append(f"Missing required file: {rf}")

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        return False

    # 2. Load JSON files
    with open(synthetic_dir / "erp_orders.json", "r", encoding="utf-8") as f:
        erp_data = json.load(f)
    with open(synthetic_dir / "gateway_transactions.json", "r", encoding="utf-8") as f:
        gtw_data = json.load(f)
    with open(synthetic_dir / "gateway_settlements.json", "r", encoding="utf-8") as f:
        stl_data = json.load(f)
    with open(synthetic_dir / "bank_transactions.json", "r", encoding="utf-8") as f:
        bnk_data = json.load(f)
    with open(ground_truth_dir / "ground_truth.json", "r", encoding="utf-8") as f:
        gt_data = json.load(f)

    # 3. Model validation
    try:
        erp_orders = [ERPOrder(**item) for item in erp_data]
        gateway_txns = [GatewayTransaction(**item) for item in gtw_data]
        settlements = [GatewaySettlement(**item) for item in stl_data]
        bank_txns = [BankTransaction(**item) for item in bnk_data]
        ground_truth = [GroundTruthCase(**item) for item in gt_data]
    except Exception as e:
        errors.append(f"Pydantic model validation failed: {e}")
        for err in errors:
            print(f"ERROR: {err}")
        return False

    # 4. Check record counts
    if len(erp_orders) < 100:
        errors.append(f"ERP orders count {len(erp_orders)} is less than 100")
    if len(gateway_txns) < 100:
        errors.append(f"Gateway transactions count {len(gateway_txns)} is less than 100")
    if len(settlements) < 50:
        errors.append(f"Gateway settlements count {len(settlements)} is less than 50")
    if len(bank_txns) < 70:
        errors.append(f"Bank transactions count {len(bank_txns)} is less than expected minimum")

    # 5. Check ground-truth isolation (ensure NO leakage fields in raw data)
    leak_fields = {"true_match", "actual_root_cause", "expected_relationship", "case_id", "is_exception"}
    for item in erp_data + gtw_data + stl_data + bnk_data:
        found_leaks = set(item.keys()).intersection(leak_fields)
        if found_leaks:
            errors.append(f"Ground truth leak in raw data! Fields found: {found_leaks}")
            break

    # 6. ID uniqueness where required
    erp_ids = set()
    for e in erp_orders:
        if e.order_id in erp_ids:
            errors.append(f"Duplicate ERP order_id: {e.order_id}")
        erp_ids.add(e.order_id)

    stl_ids = set()
    for s in settlements:
        if s.settlement_id in stl_ids:
            errors.append(f"Duplicate settlement_id: {s.settlement_id}")
        stl_ids.add(s.settlement_id)

    bnk_ids = set()
    for b in bank_txns:
        if b.bank_transaction_id in bnk_ids:
            errors.append(f"Duplicate bank_transaction_id: {b.bank_transaction_id}")
        bnk_ids.add(b.bank_transaction_id)

    gtw_ids = set(g.gateway_transaction_id for g in gateway_txns)

    # 7. Date format validation
    for e in erp_orders:
        try:
            datetime.strptime(e.order_date, "%Y-%m-%d")
        except ValueError:
            errors.append(f"Invalid date format in ERP {e.order_id}: {e.order_date}")

    for b in bank_txns:
        try:
            datetime.strptime(b.transaction_date, "%Y-%m-%d")
        except ValueError:
            errors.append(f"Invalid date format in Bank {b.bank_transaction_id}: {b.transaction_date}")

    # 8. Bank balance sequential arithmetic validation
    for i in range(1, len(bank_txns)):
        prev = bank_txns[i - 1]
        curr = bank_txns[i]
        expected_bal = round_currency(prev.balance + curr.credit_amount - curr.debit_amount)
        if abs(curr.balance - expected_bal) > DEFAULT_ROUNDING_TOLERANCE:
            errors.append(
                f"Bank balance arithmetic mismatch at {curr.bank_transaction_id}: "
                f"got {curr.balance}, expected {expected_bal} (prev={prev.balance}, credit={curr.credit_amount}, debit={curr.debit_amount})"
            )
            break

    # 9. Settlement totals consistency
    gtw_by_id = {g.gateway_transaction_id: g for g in gateway_txns}
    for s in settlements:
        # Check referenced transaction IDs exist
        for tx_id in s.transaction_ids:
            if tx_id not in gtw_by_id:
                errors.append(f"Settlement {s.settlement_id} references nonexistent transaction: {tx_id}")

        expected_gross = round_currency(sum(gtw_by_id[t].captured_amount for t in s.transaction_ids if t in gtw_by_id))
        if abs(s.gross_amount - expected_gross) > DEFAULT_ROUNDING_TOLERANCE:
            errors.append(
                f"Settlement {s.settlement_id} gross_amount {s.gross_amount} != sum of transactions {expected_gross}"
            )

        expected_net = round_currency(s.gross_amount - s.total_mdr - s.total_gst - s.refunds - s.chargebacks)
        if abs(s.net_settlement - expected_net) > DEFAULT_ROUNDING_TOLERANCE:
            errors.append(
                f"Settlement {s.settlement_id} net_settlement {s.net_settlement} != gross - fees ({expected_net})"
            )

    # 10. Ground truth referential integrity
    case_ids = set()
    scenario_counts = Counter()
    for case in ground_truth:
        if case.case_id in case_ids:
            errors.append(f"Duplicate ground truth case_id: {case.case_id}")
        case_ids.add(case.case_id)
        scenario_counts[case.scenario] += 1

        # Check all referenced ERP IDs exist
        for eid in case.erp_order_ids:
            if eid not in erp_ids:
                errors.append(f"Case {case.case_id} references nonexistent ERP ID: {eid}")

        # Check all referenced Gateway IDs exist
        for gid in case.gateway_transaction_ids:
            if gid not in gtw_ids:
                errors.append(f"Case {case.case_id} references nonexistent Gateway ID: {gid}")

        # Check all referenced Bank IDs exist
        for bid in case.bank_transaction_ids:
            if bid not in bnk_ids:
                errors.append(f"Case {case.case_id} references nonexistent Bank ID: {bid}")

        # If MISSING_BANK, bank_transaction_ids must be empty
        if case.scenario == "MISSING_BANK" and case.bank_transaction_ids:
            errors.append(f"Case {case.case_id} is MISSING_BANK but references bank IDs: {case.bank_transaction_ids}")

        # If MISSING_ERP, erp_order_ids must be empty
        if case.scenario == "MISSING_ERP" and case.erp_order_ids:
            errors.append(f"Case {case.case_id} is MISSING_ERP but references ERP IDs: {case.erp_order_ids}")

    # Output report
    if errors:
        print("\n--- DATASET VALIDATION FAILED ---")
        for err in errors[:15]:
            print(f"  - {err}")
        if len(errors) > 15:
            print(f"  ... and {len(errors) - 15} more errors")
        return False

    print("=" * 45)
    print("      DATASET VALIDATION PASSED")
    print("=" * 45)
    print(f"ERP records:          {len(erp_orders)}")
    print(f"Gateway transactions: {len(gateway_txns)}")
    print(f"Gateway settlements:  {len(settlements)}")
    print(f"Bank transactions:    {len(bank_txns)}")
    print(f"Ground truth cases:   {len(ground_truth)}")
    print("\nScenarios:")
    for sc, count in sorted(scenario_counts.items()):
        print(f"  {sc:<20} {count:>4}")
    print("-" * 45)
    print("Validation: PASSED (Zero integrity or referential errors)")
    print("=" * 45)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate Recon-AI synthetic dataset")
    parser.add_argument("--data-dir", type=str, default="data", help="Path to data directory")
    args = parser.parse_args()

    success = validate_dataset(Path(args.data_dir))
    sys.exit(0 if success else 1)
