"""Finance Route."""
from fastapi import APIRouter

from backend.app.api.schemas.finance import FinancialSummaryResponse, CashPositionResponse, CashForecastResponse
from backend.app.services.reconciliation_service import reconciliation_service
from backend.app.finance.cash_position import calculate_cash_position
from backend.app.finance.forecast import calculate_cash_forecast

router = APIRouter()

@router.get("/financial-summary", response_model=FinancialSummaryResponse)
def get_financial_summary():
    """Retrieves the overall financial summary of the latest reconciliation run."""
    return reconciliation_service.get_financial_summary()

@router.get("/cash-position", response_model=CashPositionResponse)
def get_cash_position():
    """Retrieves the deterministic cash position based on the latest run data."""
    latest_run_data = reconciliation_service.get_latest_run_data()
    return calculate_cash_position(latest_run_data)

@router.get("/cash-forecast", response_model=CashForecastResponse)
def get_cash_forecast():
    """Retrieves the deterministic cash forecast based on the latest run data."""
    latest_run_data = reconciliation_service.get_latest_run_data()
    return calculate_cash_forecast(latest_run_data)
