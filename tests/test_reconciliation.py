"""Tests for the Recon-AI Deterministic Reconciliation Engine."""

import sys
from pathlib import Path
import pytest

from backend.app.data_generation.generator import SyntheticDataGenerator
from backend.app.reconciliation.engine import ReconciliationEngine
from backend.app.reconciliation.types import MatchType, ReconciliationStatus, RootCause

def test_engine_no_ground_truth_dependency():
    """Verify engine has NO dependency on ground_truth module or directory."""
    import sys
    engine = ReconciliationEngine()
    
    # Assert ground_truth module is not in imported modules for reconciliation
    # The generator uses it, but engine should not.
    assert "backend.app.data_generation.ground_truth" not in sys.modules
    
    # Simple check that the engine does not accept ground truth as input
    import inspect
    sig = inspect.signature(engine.reconcile)
    assert "ground_truth" not in sig.parameters

def test_100_record_reconciliation_integration():
    """Run reconciliation on 100 synthetic records and check bounds."""
    generator = SyntheticDataGenerator(seed=42)
    erp_orders, gateway_txns, settlements, bank_txns, gt = generator.generate_dataset(100)
    
    engine = ReconciliationEngine()
    result = engine.reconcile(erp_orders, gateway_txns, settlements, bank_txns)
    
    summary = result["summary"]
    
    # Validate processed transactions count matches input
    assert summary["records_processed"] == len(gateway_txns)
    
    # Ensure all required root causes were found in some capacity
    results_list = result["reconciliation_results"]
    root_causes_found = set(r.root_cause for r in results_list)
    
    assert RootCause.EXACT_MATCH in root_causes_found
    assert RootCause.MDR_GST in root_causes_found
    assert RootCause.BATCH_SETTLEMENT in root_causes_found
    assert RootCause.MISSING_BANK in root_causes_found
    assert RootCause.MISSING_ERP in root_causes_found
    
    # Check no double matching: every gateway ID is assigned at most once
    used_gids = []
    for r in results_list:
        used_gids.extend(r.gateway_transaction_ids)
    
    assert len(used_gids) == len(set(used_gids)), "Duplicate assignment detected! Same gateway ID used multiple times."

def test_500_record_reconciliation_scaling():
    """Run reconciliation on 500 synthetic records and ensure reasonable execution time."""
    import time
    generator = SyntheticDataGenerator(seed=42)
    erp_orders, gateway_txns, settlements, bank_txns, _ = generator.generate_dataset(500)
    
    engine = ReconciliationEngine()
    start_time = time.time()
    result = engine.reconcile(erp_orders, gateway_txns, settlements, bank_txns)
    elapsed_ms = (time.time() - start_time) * 1000.0
    
    summary = result["summary"]
    assert summary["records_processed"] == len(gateway_txns)
    assert elapsed_ms < 2000.0, f"Engine took too long for 500 records: {elapsed_ms}ms"

def test_tier1_exact_match_priority():
    """Verify tier 1 exact matching prioritizes strong IDs."""
    generator = SyntheticDataGenerator(seed=99)
    erp_orders, gateway_txns, settlements, bank_txns, gt = generator.generate_dataset(20)
    
    engine = ReconciliationEngine()
    result = engine.reconcile(erp_orders, gateway_txns, settlements, bank_txns)
    
    # Look for exact 1:1 match
    exact_matches = [r for r in result["reconciliation_results"] if r.match_type == MatchType.EXACT_1_TO_1]
    
    for r in exact_matches:
        if r.confidence >= 0.95:
            assert r.status == ReconciliationStatus.RESOLVED
        else:
            assert r.status == ReconciliationStatus.REVIEW
        
        assert len(r.gateway_transaction_ids) == 1
        assert len(r.bank_transaction_ids) == 1
        assert "exact" in r.evidence.matched_by[0]
        
def test_exceptions_detector_missing_bank():
    """Verify missing bank exception behaves safely and doesn't hallucinate bank records."""
    generator = SyntheticDataGenerator(seed=42)
    erp_orders, gateway_txns, settlements, bank_txns, gt = generator.generate_dataset(100)
    
    engine = ReconciliationEngine()
    result = engine.reconcile(erp_orders, gateway_txns, settlements, bank_txns)
    
    missing_bank_results = [r for r in result["reconciliation_results"] if r.root_cause == RootCause.MISSING_BANK]
    
    assert len(missing_bank_results) > 0
    for r in missing_bank_results:
        assert len(r.bank_transaction_ids) == 0
        assert r.actual_amount == 0.0
        assert r.difference == r.expected_amount
        assert r.status == ReconciliationStatus.REVIEW

def test_exceptions_detector_missing_erp():
    """Verify missing ERP exception doesn't fabricate ERP records."""
    generator = SyntheticDataGenerator(seed=42)
    erp_orders, gateway_txns, settlements, bank_txns, gt = generator.generate_dataset(100)
    
    engine = ReconciliationEngine()
    result = engine.reconcile(erp_orders, gateway_txns, settlements, bank_txns)
    
    missing_erp_results = [r for r in result["reconciliation_results"] if r.root_cause == RootCause.MISSING_ERP]
    
    assert len(missing_erp_results) > 0
    for r in missing_erp_results:
        assert len(r.erp_order_ids) == 0
        assert r.status == ReconciliationStatus.REVIEW
