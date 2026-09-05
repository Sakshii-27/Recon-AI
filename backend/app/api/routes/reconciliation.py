"""Reconciliation Route."""
from fastapi import APIRouter, HTTPException

from backend.app.api.schemas.reconciliation import ReconciliationRunRequest, ReconciliationResponse, ReconciliationSummary
from backend.app.services.reconciliation_service import reconciliation_service

router = APIRouter()

@router.post("/run", response_model=ReconciliationResponse)
def run_reconciliation(request: ReconciliationRunRequest):
    """Runs a deterministic reconciliation batch and caches the latest results."""
    try:
        return reconciliation_service.run_reconciliation(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine failure: {str(e)}")

@router.get("/summary", response_model=ReconciliationSummary)
def get_reconciliation_summary():
    """Retrieves the summary of the latest reconciliation run."""
    summary = reconciliation_service.get_summary()
    if not summary:
        raise HTTPException(status_code=404, detail="No run found")
    return summary
