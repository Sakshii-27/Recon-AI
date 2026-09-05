"""Exceptions Route."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from backend.app.api.schemas.exceptions import ExceptionListResponse, ExceptionDetail
from backend.app.services.reconciliation_service import reconciliation_service

router = APIRouter()

@router.get("", response_model=ExceptionListResponse)
def list_exceptions(type: Optional[str] = Query(None, description="Filter by exception type/root cause")):
    """Retrieves exceptions from the latest reconciliation run."""
    return reconciliation_service.get_exceptions(type_filter=type)


@router.get("/{exception_id}", response_model=ExceptionDetail)
def get_exception(exception_id: str):
    """Retrieves detailed evidence for a specific exception."""
    exception = reconciliation_service.get_exception(exception_id)
    if not exception:
        raise HTTPException(status_code=404, detail=f"Exception {exception_id} not found in latest run")
    return exception
