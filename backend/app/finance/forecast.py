"""Cash Forecast Engine.

Deterministically calculates expected future cash inflows based strictly on 
explicit settlement_date fields generated in the synthetic dataset.
"""

from typing import Dict, Any
from collections import defaultdict
from datetime import datetime, timedelta

from backend.app.api.schemas.finance import CashForecastResponse, DailyForecast
from backend.app.domain.finance_rules import calculate_expected_net_settlement
from backend.app.reconciliation.types import ReconciliationStatus


def calculate_cash_forecast(latest_run_data: Dict[str, Any]) -> CashForecastResponse:
    if not latest_run_data:
        return CashForecastResponse()

    bank_txns = latest_run_data.get("bank_txns", [])
    gateway_txns = latest_run_data.get("gateway_txns", [])
    raw_results = latest_run_data.get("raw_results", [])

    # 1. Determine "today" based on the latest date in the bank records
    if not bank_txns:
        return CashForecastResponse()
        
    latest_bank_date_str = bank_txns[-1].transaction_date
    latest_bank_date = datetime.strptime(latest_bank_date_str, "%Y-%m-%d")

    # 2. Identify Gateway Transactions that are NOT yet successfully reconciled
    # We don't want to forecast cash that has already arrived and been reconciled.
    reconciled_gtw_ids = set()
    for r in raw_results:
        if r.status == ReconciliationStatus.RESOLVED:
            reconciled_gtw_ids.update(r.gateway_transaction_ids)

    # 3. Aggregate future expected settlements by date
    future_inflows = defaultdict(float)
    
    for gtw in gateway_txns:
        if gtw.gateway_transaction_id in reconciled_gtw_ids:
            continue
            
        if not gtw.settlement_date:
            continue
            
        settlement_date = datetime.strptime(gtw.settlement_date, "%Y-%m-%d")
        
        # Only forecast if the settlement date is strictly strictly greater than our deterministic "today",
        # or if it's equal but missing from the bank (which means it will hopefully arrive tomorrow).
        # We'll forecast anything >= today that isn't resolved, placing it in the future.
        if settlement_date > latest_bank_date:
            net = calculate_expected_net_settlement(
                gtw.captured_amount,
                refund_amount=gtw.refund_amount,
                chargeback_amount=gtw.chargeback_amount
            )
            future_inflows[gtw.settlement_date] += net
        elif settlement_date <= latest_bank_date:
            # Overdue! Forecast it for tomorrow as a delayed arrival
            tomorrow_str = (latest_bank_date + timedelta(days=1)).strftime("%Y-%m-%d")
            net = calculate_expected_net_settlement(
                gtw.captured_amount,
                refund_amount=gtw.refund_amount,
                chargeback_amount=gtw.chargeback_amount
            )
            future_inflows[tomorrow_str] += net

    # 4. Generate the 7-day and 14-day sequence
    forecast_7_day = []
    forecast_14_day = []
    
    cumulative_cash = 0.0
    
    for i in range(1, 15):
        target_date = latest_bank_date + timedelta(days=i)
        target_date_str = target_date.strftime("%Y-%m-%d")
        
        inflow = future_inflows.get(target_date_str, 0.0)
        cumulative_cash += inflow
        
        daily = DailyForecast(
            date=target_date_str,
            expected_inflow=inflow,
            expected_outflow=0.0,
            net_cash_change=inflow,
            cumulative_expected_cash=cumulative_cash,
            confidence="HIGH" if inflow > 0 else "N/A",
            basis="deterministic_expected_settlement" if inflow > 0 else "no_scheduled_settlements"
        )
        
        if i <= 7:
            forecast_7_day.append(daily)
        forecast_14_day.append(daily)
        
    return CashForecastResponse(
        forecast_7_day=forecast_7_day,
        forecast_14_day=forecast_14_day
    )
