"""Cash Position Engine.

Deterministically calculates actual, expected, pending, and at-risk cash 
based strictly on the available synthetic dataset and reconciliation output.
"""

from typing import Dict, Any, List
from backend.app.api.schemas.finance import CashPositionResponse
from backend.app.reconciliation.types import ReconciliationStatus
from backend.app.domain.finance_rules import calculate_expected_net_settlement

def calculate_cash_position(latest_run_data: Dict[str, Any]) -> CashPositionResponse:
    if not latest_run_data:
        return CashPositionResponse()

    raw_results = latest_run_data.get("raw_results", [])
    bank_txns = latest_run_data.get("bank_txns", [])
    gateway_txns = latest_run_data.get("gateway_txns", [])

    # 1. bank_cash: The latest valid chronological balance
    bank_cash = 0.0
    if bank_txns:
        # Assuming bank_txns is already chronologically sorted by the generator
        bank_cash = bank_txns[-1].balance

    # 2. gateway_captured & gateway_net_expected
    gateway_captured = 0.0
    gateway_net_expected = 0.0
    for gtw in gateway_txns:
        gateway_captured += gtw.captured_amount
        net = calculate_expected_net_settlement(
            gtw.captured_amount, 
            refund_amount=gtw.refund_amount, 
            chargeback_amount=gtw.chargeback_amount
        )
        gateway_net_expected += net

    # We need to track which gateway transactions are in which buckets to avoid double-counting.
    # Gateway IDs successfully reconciled
    reconciled_gateway_ids = set()
    reconciled_cash = 0.0

    # Gateway IDs tied up in exceptions
    exception_gateway_ids = set()
    exception_value = 0.0
    cash_at_risk = 0.0
    pending_settlement = 0.0

    # Exception types that directly indicate cash is delayed or at risk
    risk_exception_types = {"CHARGEBACK", "FEE_ANOMALY", "MISSING_BANK", "MISSING_ERP", "PARTIAL_SETTLEMENT"}
    
    # 3. Process reconciliation results safely
    for r in raw_results:
        result_gtw_ids = set(r.gateway_transaction_ids)
        result_expected_net = r.expected_amount or 0.0

        if r.status == ReconciliationStatus.RESOLVED:
            reconciled_cash += abs(r.actual_amount)
            reconciled_gateway_ids.update(result_gtw_ids)
        else:
            root_cause = r.root_cause.value if r.root_cause else "UNKNOWN"
            
            # Avoid double counting if a transaction somehow spans multiple exceptions
            new_ids = result_gtw_ids - exception_gateway_ids - reconciled_gateway_ids
            if new_ids:
                exception_gateway_ids.update(new_ids)
                exception_value += abs(result_expected_net)
                
                # MISSING_BANK directly means gateway expected it, but it didn't hit the bank
                if root_cause == "MISSING_BANK":
                    pending_settlement += abs(result_expected_net)
                    cash_at_risk += abs(result_expected_net)
                elif root_cause in risk_exception_types:
                    cash_at_risk += abs(result_expected_net)

    # Calculate coverage
    reconciliation_coverage = 0.0
    if gateway_net_expected > 0:
        reconciliation_coverage = (reconciled_cash / gateway_net_expected) * 100.0

    return CashPositionResponse(
        bank_cash=bank_cash,
        gateway_captured=gateway_captured,
        gateway_net_expected=gateway_net_expected,
        reconciled_cash=reconciled_cash,
        pending_settlement=pending_settlement,
        exception_value=exception_value,
        cash_at_risk=cash_at_risk,
        reconciliation_coverage=reconciliation_coverage
    )
