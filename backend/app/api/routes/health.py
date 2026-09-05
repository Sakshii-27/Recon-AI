"""Health Check Route."""
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    """Returns application health status."""
    return {"status": "ok", "service": "ReconPulse AI API"}
