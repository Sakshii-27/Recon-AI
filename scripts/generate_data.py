#!/usr/bin/env python3
"""CLI script to generate synthetic financial datasets with isolated ground truth for Recon-AI."""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path so backend package is importable
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.data_generation.generator import (
    SyntheticDataGenerator,
    save_dataset_to_disk,
)
from backend.app.domain.finance_rules import DEFAULT_SEED


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate synthetic financial dataset for Recon-AI"
    )
    parser.add_argument(
        "--records",
        type=int,
        default=100,
        help="Number of scenario cases to generate (default: 100)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"Random seed for reproducibility (default: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Root output directory for data (default: 'data')",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"Generating synthetic financial dataset with {args.records} cases (seed={args.seed})...")

    generator = SyntheticDataGenerator(seed=args.seed)
    (
        erp_orders,
        gateway_txns,
        settlements,
        bank_txns,
        ground_truth,
    ) = generator.generate_dataset(total_cases=args.records)

    out_path = Path(args.output_dir)
    save_dataset_to_disk(
        erp_orders=erp_orders,
        gateway_txns=gateway_txns,
        settlements=settlements,
        bank_txns=bank_txns,
        ground_truth=ground_truth,
        output_dir=out_path,
    )

    print("\nGeneration Complete:")
    print(f"  ERP Orders:            {len(erp_orders)}")
    print(f"  Gateway Transactions:  {len(gateway_txns)}")
    print(f"  Gateway Settlements:   {len(settlements)}")
    print(f"  Bank Transactions:     {len(bank_txns)}")
    print(f"  Ground Truth Cases:    {len(ground_truth)}")
    print(f"\nFiles saved to:\n  - {out_path / 'synthetic'} (JSON + CSV)\n  - {out_path / 'ground_truth'} (JSON)")


if __name__ == "__main__":
    main()
