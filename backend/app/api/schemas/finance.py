"""Financial API Schemas."""
from typing import Any, Dict
from pydantic import BaseModel, Field


class FinancialSummaryResponse(BaseModel):
    """Overall financial summary of the reconciliation run."""
    gross_sales: float = Field(default=0.0, description="Total expected gross sales across all transactions")
    gateway_captured: float = Field(default=0.0, description="Total amount captured by the gateway")
    gateway_fees: float = Field(default=0.0, description="Total MDR fees charged")
    gateway_gst: float = Field(default=0.0, description="Total GST on MDR fees")
    expected_settlement: float = Field(default=0.0, description="Expected net settlement into the bank")
    bank_settlement: float = Field(default=0.0, description="Actual bank settlement received")
    unreconciled_value: float = Field(default=0.0, description="Total value left unresolved or disputed")

class CashPositionResponse(BaseModel):
    """Deterministic cash position calculated from existing reconciliation data."""
    bank_cash: float = Field(default=0.0, description="Latest valid chronological balance from the bank records")
    gateway_captured: float = Field(default=0.0, description="Total gross captured by the gateway")
    gateway_net_expected: float = Field(default=0.0, description="Total deterministically expected net payout across gateway transactions")
    reconciled_cash: float = Field(default=0.0, description="Financial value for which the expected gateway/settlement flow has been successfully established against bank records")
    pending_settlement: float = Field(default=0.0, description="Expected net value for gateway transactions confirmed but missing from bank (e.g. MISSING_BANK exception)")
    exception_value: float = Field(default=0.0, description="Monetary value associated with unresolved exceptions where exposure is safely calculable")
    cash_at_risk: float = Field(default=0.0, description="Subset of exception value indicating direct cash impact (e.g., CHARGEBACK, FEE_ANOMALY, MISSING_ERP, MISSING_BANK)")
    reconciliation_coverage: float = Field(default=0.0, description="Percentage of gateway net expected that is either reconciled or safely accounted for")

class DailyForecast(BaseModel):
    date: str
    expected_inflow: float = 0.0
    expected_outflow: float = 0.0
    net_cash_change: float = 0.0
    cumulative_expected_cash: float = 0.0
    confidence: str = Field(..., description="E.g., HIGH, LOW")
    basis: str = Field(..., description="Source of the forecast (e.g., deterministic_expected_settlement)")

class CashForecastResponse(BaseModel):
    """Deterministic forecast of expected future cash flows based on explicit settlement dates."""
    forecast_7_day: list[DailyForecast] = []
    forecast_14_day: list[DailyForecast] = []
