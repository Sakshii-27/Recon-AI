"""Comprehensive test suite for synthetic dataset generator and ground truth isolation."""

import json
from pathlib import Path
import pytest

from backend.app.data_generation.generator import SyntheticDataGenerator, save_dataset_to_disk
from backend.app.data_generation.scenarios import ScenarioType
from backend.app.domain.finance_rules import calculate_total_fee, round_currency


def test_1_same_seed_produces_identical_dataset():
    """Test 1: Same seed -> same dataset."""
    gen1 = SyntheticDataGenerator(seed=42)
    erp1, gtw1, stl1, bnk1, gt1 = gen1.generate_dataset(100)

    gen2 = SyntheticDataGenerator(seed=42)
    erp2, gtw2, stl2, bnk2, gt2 = gen2.generate_dataset(100)

    assert len(erp1) == len(erp2)
    assert len(gtw1) == len(gtw2)
    assert len(bnk1) == len(bnk2)
    assert len(gt1) == len(gt2)

    assert [e.model_dump() for e in erp1] == [e.model_dump() for e in erp2]
    assert [g.model_dump() for g in gtw1] == [g.model_dump() for g in gtw2]
    assert [b.model_dump() for b in bnk1] == [b.model_dump() for b in bnk2]
    assert [x.model_dump() for x in gt1] == [x.model_dump() for x in gt2]


def test_2_different_seed_produces_different_dataset():
    """Test 2: Different seed -> different dataset."""
    gen1 = SyntheticDataGenerator(seed=42)
    erp1, _, _, bnk1, _ = gen1.generate_dataset(100)

    gen2 = SyntheticDataGenerator(seed=99)
    erp2, _, _, bnk2, _ = gen2.generate_dataset(100)

    assert [e.order_reference for e in erp1] != [e.order_reference for e in erp2]
    assert [b.reference for b in bnk1] != [b.reference for b in bnk2]


def test_3_volume_meets_or_exceeds_minimum():
    """Test 3: 100 records requested -> at least 100 generated across all sources."""
    gen = SyntheticDataGenerator(seed=42)
    erp, gtw, stl, bnk, gt = gen.generate_dataset(100)

    assert len(erp) >= 100
    assert len(gtw) >= 100
    assert len(stl) >= 50
    assert len(bnk) >= 70
    assert len(gt) == 100


def test_4_all_required_scenarios_exist():
    """Test 4: All required scenario types exist in the generated dataset."""
    gen = SyntheticDataGenerator(seed=42)
    _, _, _, _, gt = gen.generate_dataset(100)

    scenarios_found = set(case.scenario for case in gt)
    for expected_scenario in ScenarioType:
        assert expected_scenario.value in scenarios_found, f"Missing scenario: {expected_scenario}"


def test_5_ground_truth_references_valid_ids():
    """Test 5: Ground truth references valid source IDs (referential integrity)."""
    gen = SyntheticDataGenerator(seed=42)
    erp, gtw, stl, bnk, gt = gen.generate_dataset(100)

    erp_ids = set(e.order_id for e in erp)
    gtw_ids = set(g.gateway_transaction_id for g in gtw)
    bnk_ids = set(b.bank_transaction_id for b in bnk)

    for case in gt:
        for eid in case.erp_order_ids:
            assert eid in erp_ids, f"Invalid ERP ID {eid} in case {case.case_id}"
        for gid in case.gateway_transaction_ids:
            assert gid in gtw_ids, f"Invalid Gateway ID {gid} in case {case.case_id}"
        for bid in case.bank_transaction_ids:
            assert bid in bnk_ids, f"Invalid Bank ID {bid} in case {case.case_id}"


def test_6_normal_mdr_gst_calculations_are_correct():
    """Test 6: Normal MDR + GST calculations are mathematically accurate."""
    gen = SyntheticDataGenerator(seed=42)
    _, gtw, _, _, gt = gen.generate_dataset(100)

    gtw_map = {g.gateway_transaction_id: g for g in gtw}
    mdr_cases = [c for c in gt if c.scenario == ScenarioType.MDR_GST.value]

    assert len(mdr_cases) > 0
    for case in mdr_cases:
        tx = gtw_map[case.gateway_transaction_ids[0]]
        expected_mdr, expected_gst, _ = calculate_total_fee(tx.captured_amount, 0.02, 0.18)
        assert tx.gateway_fee == expected_mdr
        assert tx.gst_on_fee == expected_gst
        expected_net = round_currency(tx.captured_amount - expected_mdr - expected_gst)
        assert case.expected_net_amount == expected_net


def test_7_bank_balance_arithmetic_is_correct():
    """Test 7: Bank balance arithmetic is strictly sequential and verified."""
    gen = SyntheticDataGenerator(seed=42)
    _, _, _, bnk, _ = gen.generate_dataset(100)

    assert len(bnk) > 1
    for i in range(1, len(bnk)):
        prev = bnk[i - 1]
        curr = bnk[i]
        expected_balance = round_currency(prev.balance + curr.credit_amount - curr.debit_amount)
        assert abs(curr.balance - expected_balance) < 0.001


def test_8_batch_settlement_totals_are_correct():
    """Test 8: Batch settlement totals correctly aggregate multiple transactions."""
    gen = SyntheticDataGenerator(seed=42)
    _, gtw, stl, _, gt = gen.generate_dataset(100)

    gtw_map = {g.gateway_transaction_id: g for g in gtw}
    stl_map = {s.settlement_id: s for s in stl}
    batch_cases = [c for c in gt if c.scenario == ScenarioType.BATCH_SETTLEMENT.value]

    assert len(batch_cases) > 0
    for case in batch_cases:
        assert len(case.gateway_transaction_ids) >= 2
        settlement = stl_map[case.settlement_id]
        total_gross = round_currency(sum(gtw_map[t].captured_amount for t in case.gateway_transaction_ids))
        total_mdr = round_currency(sum(gtw_map[t].gateway_fee for t in case.gateway_transaction_ids))
        total_gst = round_currency(sum(gtw_map[t].gst_on_fee for t in case.gateway_transaction_ids))

        assert settlement.gross_amount == total_gross
        assert settlement.total_mdr == total_mdr
        assert settlement.total_gst == total_gst
        assert settlement.net_settlement == round_currency(total_gross - total_mdr - total_gst)


def test_9_missing_bank_cases_have_no_bank_transaction():
    """Test 9: Missing-bank cases genuinely have no corresponding bank transaction."""
    gen = SyntheticDataGenerator(seed=42)
    _, _, _, bnk, gt = gen.generate_dataset(100)

    missing_bank_cases = [c for c in gt if c.scenario == ScenarioType.MISSING_BANK.value]
    assert len(missing_bank_cases) > 0

    all_bank_ids = set(b.bank_transaction_id for b in bnk)
    all_bank_refs = set(b.reference for b in bnk)

    for case in missing_bank_cases:
        assert len(case.bank_transaction_ids) == 0
        assert case.actual_bank_amount is None
        assert case.is_exception is True
        assert case.root_cause == "MISSING_BANK"
        # Ensure settlement ID doesn't appear in bank references
        if case.settlement_id:
            assert case.settlement_id not in all_bank_refs


def test_10_ground_truth_does_not_leak_into_source_data(tmp_path: Path):
    """Test 10: Ground truth fields do not leak into raw source JSON/CSV files."""
    gen = SyntheticDataGenerator(seed=42)
    erp, gtw, stl, bnk, gt = gen.generate_dataset(100)

    save_dataset_to_disk(erp, gtw, stl, bnk, gt, tmp_path)

    synthetic_dir = tmp_path / "synthetic"
    leak_keys = {"true_match", "actual_root_cause", "expected_relationship", "case_id", "is_exception"}

    for filename in ["erp_orders.json", "gateway_transactions.json", "gateway_settlements.json", "bank_transactions.json"]:
        with open(synthetic_dir / filename, "r", encoding="utf-8") as f:
            records = json.load(f)
            for record in records:
                intersection = set(record.keys()).intersection(leak_keys)
                assert not intersection, f"Leak found in {filename}: {intersection}"
