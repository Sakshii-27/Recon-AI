"""Tests for deterministic Cash Position and Forecast Engine."""

import pytest
from backend.app.data_generation.generator import SyntheticDataGenerator
from backend.app.reconciliation.engine import ReconciliationEngine
from backend.app.finance.cash_position import calculate_cash_position
from backend.app.finance.forecast import calculate_cash_forecast

@pytest.fixture
def run_reconciliation():
    # Uses the same reproducible seed to ensure the numbers are exact.
    generator = SyntheticDataGenerator(seed=42)
    erp_orders, gateway_txns, settlements, bank_txns, ground_truth = generator.generate_dataset(100)
    
    engine = ReconciliationEngine()
    engine_output = engine.reconcile(erp_orders, gateway_txns, settlements, bank_txns)
    
    latest_run_data = {
        "raw_results": engine_output["reconciliation_results"],
        "bank_txns": bank_txns,
        "gateway_txns": gateway_txns,
        "erp_orders": erp_orders,
        "settlements": settlements
    }
    return latest_run_data

def test_cash_position_deterministic(run_reconciliation):
    latest_run_data = run_reconciliation
    position = calculate_cash_position(latest_run_data)
    
    # These should be strictly populated
    assert position.bank_cash > 0
    assert position.gateway_captured > 0
    assert position.gateway_net_expected > 0
    assert position.reconciled_cash > 0
    
    # We shouldn't double count. exception_value + reconciled_cash should approximately cover the universe
    # but there may be edge cases based on matching strategy.
    # We must explicitly ensure pending_settlement <= exception_value
    assert position.pending_settlement <= position.exception_value
    
    # Cash at risk is a subset of exception value
    assert position.cash_at_risk <= position.exception_value
    
    # Ensure percentages make sense
    assert 0.0 <= position.reconciliation_coverage <= 100.0

def test_forecast_deterministic(run_reconciliation):
    latest_run_data = run_reconciliation
    forecast = calculate_cash_forecast(latest_run_data)
    
    assert len(forecast.forecast_7_day) == 7
    assert len(forecast.forecast_14_day) == 14
    
    # Cumulative should monotonically increase or stay flat
    prev_cum = 0.0
    for day in forecast.forecast_7_day:
        assert day.expected_inflow >= 0
        assert day.cumulative_expected_cash >= prev_cum
        assert day.confidence in ("HIGH", "N/A")
        assert day.basis in ("deterministic_expected_settlement", "no_scheduled_settlements")
        prev_cum = day.cumulative_expected_cash

def test_empty_data():
    position = calculate_cash_position({})
    assert position.bank_cash == 0.0
    assert position.gateway_captured == 0.0
    
    forecast = calculate_cash_forecast({})
    assert len(forecast.forecast_7_day) == 0
